export default {
  async fetch(request, env) {
    const origin  = request.headers.get("Origin") || "";
    const allowed = "https://rahulrayy.github.io";

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin, allowed),
      });
    }

    if (request.method !== "POST") {
      return jsonResp({ error: "method not allowed" }, 405, origin, allowed);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResp({ error: "invalid json" }, 400, origin, allowed);
    }

    const { email, honeypot } = body;

    if (honeypot) {
      return jsonResp({ ok: true }, 200, origin, allowed);
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return jsonResp({ error: "invalid email" }, 400, origin, allowed);
    }

    const brevoResp = await fetch(
      "https://api.brevo.com/v3/contacts",
      {
        method:  "POST",
        headers: {
          "api-key":      env.BREVO_API_KEY,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          updateEnabled: true,
        }),
      }
    );

    if (brevoResp.ok || brevoResp.status === 204) {
      return jsonResp({ ok: true }, 200, origin, allowed);
    }

    return jsonResp({ error: "subscription failed" }, 500, origin, allowed);
  },
};

function corsHeaders(origin, allowed) {
  return {
    "Access-Control-Allow-Origin":  origin === allowed ? allowed : "",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResp(body, status, origin, allowed) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin, allowed) },
  });
}