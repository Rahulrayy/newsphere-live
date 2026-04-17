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

    const { email, turnstileToken, honeypot } = body;

    if (honeypot) {
      return jsonResp({ ok: true }, 200, origin, allowed);
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return jsonResp({ error: "invalid email" }, 400, origin, allowed);
    }

    const tsResp = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          secret:   env.TURNSTILE_SECRET_KEY,
          response: turnstileToken,
        }),
      }
    );
    const { success } = await tsResp.json();
    if (!success) {
      return jsonResp({ error: "turnstile verification failed" }, 403, origin, allowed);
    }

    const rsResp = await fetch(
      `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
      {
        method:  "POST",
        headers: {
          Authorization:  `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, unsubscribed: false }),
      }
    );

    if (rsResp.ok || rsResp.status === 409) {
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