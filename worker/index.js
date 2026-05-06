export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const { question } = await request.json();
    if (!question) {
      return new Response(JSON.stringify({ error: "missing question" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const indexUrl = `${env.SITE_URL}/static/contentIndex.json`;
    const indexResp = await fetch(indexUrl);
    if (!indexResp.ok) {
      return new Response(JSON.stringify({ error: "failed to fetch content index" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }

    const contentIndex = await indexResp.json();

    const keywords = question
      .toLowerCase()
      .split(/[\s,，。？?!！、]+/)
      .filter((w) => w.length > 1);

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

    const aiResp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
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
      const err = await aiResp.text();
      return jsonResp({ answer: `AI 服务暂时不可用，请稍后重试。`, sources: scored.map((s) => s.title) });
    }

    const aiData = await aiResp.json();
    const answer = aiData.choices?.[0]?.message?.content || "无法生成回答";

    return jsonResp({
      answer,
      sources: scored.map((s) => ({ title: s.title, slug: s.slug })),
    });
  },
};

function jsonResp(data) {
  return new Response(JSON.stringify(data), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
