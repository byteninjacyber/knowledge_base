const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405, headers: CORS });
    }

    try {
      return await handlePost(request, env);
    } catch (e) {
      return jsonResp({ answer: "服务异常，请稍后重试", sources: [] }, 500);
    }
  },
};

async function handlePost(request, env) {
  const { question } = await request.json();
  if (!question) {
    return jsonResp({ error: "missing question" }, 400);
  }

  const indexUrl = `${env.SITE_URL}/static/contentIndex.json`;
  const indexResp = await fetch(indexUrl);
  if (!indexResp.ok) {
    return jsonResp({ error: "failed to fetch content index" }, 500);
  }

  const contentIndex = await indexResp.json();

  // CJK bigram tokenization (Chinese has no word boundaries)
  const raw = question
    .toLowerCase()
    .split(/[\s,，。？?!！、]+/)
    .filter((w) => w.length > 1);
  const cjkRe = /[\u4e00-\u9fff\u3400-\u4dbf]/;
  const keywords = [];
  for (const w of raw) {
    if (cjkRe.test(w)) {
      const chars = [...w];
      for (let i = 0; i < chars.length - 1; i++) {
        if (cjkRe.test(chars[i]) && cjkRe.test(chars[i + 1])) {
          keywords.push(chars[i] + chars[i + 1]);
        }
      }
      const cjkMatches = w.match(/[\u4e00-\u9fff\u3400-\u4dbf]{3,}/g);
      if (cjkMatches) keywords.push(...cjkMatches);
      const nonCjk = w.replace(/[\u4e00-\u9fff\u3400-\u4dbf]+/g, " ").trim().split(/\s+/).filter((s) => s.length > 1);
      keywords.push(...nonCjk);
    } else {
      keywords.push(w);
    }
  }

  const scored = Object.entries(contentIndex)
    .map(([slug, entry]) => {
      const text = (entry.content || "").toLowerCase();
      const title = (entry.title || "").toLowerCase();
      let score = 0;
      for (const kw of keywords) {
        if (title.includes(kw)) score += 5;
        const matches = text.split(kw).length - 1;
        score += matches;
      }
      return { slug, title: entry.title, content: entry.content, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  if (scored.length === 0) {
    return jsonResp({ answer: "知识库中没有找到相关内容。", sources: [] });
  }

  const context = scored
    .map((s) => `【${s.title}】\n${(s.content || "").slice(0, 2000)}`)
    .join("\n\n---\n\n");

  const systemPrompt = `你是一个知识库问答助手。根据提供的笔记内容回答用户问题。
规则：
1. 只基于提供的笔记内容回答，不要编造信息
2. 如果笔记中没有相关信息，明确说"知识库中没有找到相关内容"
3. 回答要简洁、准确、有条理
4. 如果涉及代码，用 markdown 代码块格式`;

  const aiResp = await fetch("https://models.inference.ai.azure.com/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${env.KB_AI_KEY}`,
    },
    body: JSON.stringify({
      model: env.AI_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `参考资料:\n${context}\n\n问题: ${question}` },
      ],
      temperature: 0.3,
    }),
  });

  if (!aiResp.ok) {
    return jsonResp({ answer: "AI 服务暂时不可用，请稍后重试。", sources: scored.map((s) => s.title) });
  }

  const aiData = await aiResp.json();
  const answer = aiData.choices?.[0]?.message?.content || "无法生成回答";

  return jsonResp({
    answer,
    sources: scored.map((s) => ({ title: s.title, slug: s.slug })),
  });
}

function jsonResp(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}
