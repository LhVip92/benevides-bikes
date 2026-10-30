async function handler(request, env) {
  function result(value, status) {
    return new Response(JSON.stringify(value), {
      status: status || 200,
      headers: { "Content-Type": "application/json" }
    });
  }
  function ignored(reason) {
    return result({ vars: { pausa_humano: { status: "ignorado", reason: reason } } });
  }
  async function api(path, patch) {
    var options = {
      method: patch ? "PATCH" : "GET",
      headers: { "X-API-Key": env.KAPSO_API_KEY, "Content-Type": "application/json" }
    };
    if (patch) options.body = JSON.stringify(patch);
    var response = await fetch("https://api.kapso.ai/platform/v1" + path, options);
    if (!response.ok) throw new Error("Kapso API HTTP " + response.status);
    return await response.json();
  }
  var target = "ac0feaf6-f912-4e5b-846e-ceb4b2721a07";
  var phoneId = "629422250252844";
  try {
    var body = await request.json();
    var context = body.execution_context || {};
    var system = context.system || {};
    var event = system.event || {};
    var payload = event.payload || event;
    var message = event.message || payload.message || {};
    var conversation = event.conversation || payload.conversation || {};
    var metadata = message.kapso || {};
    if (event.type !== "whatsapp.message.sent") return ignored("outro_evento");
    if (metadata.origin !== "business_app" || metadata.direction !== "outbound") {
      return ignored("mensagem_nao_enviada_pelo_business_app");
    }
    var phone = payload.phone_number_id || metadata.phone_number_id || conversation.phone_number_id;
    if (String(phone || "") !== phoneId) return ignored("outro_numero");
    if (typeof conversation.id !== "string" || conversation.id.length !== 36) {
      throw new Error("conversation_id ausente ou invalido");
    }
    var sentAt = Number(message.timestamp) * 1000;
    if (!isFinite(sentAt) || sentAt <= 0) sentAt = Date.parse(message.timestamp);
    if (!isFinite(sentAt)) throw new Error("timestamp invalido");
    if (Date.now() - sentAt > 120000 || sentAt - Date.now() > 30000) {
      return ignored("evento_antigo_ou_futuro");
    }
    if (system.test_mode === true || (context.context || {}).channel === "test") {
      return result({ vars: { pausa_humano: { status: "simulacao" } } });
    }
    if (!env.KAPSO_API_KEY) throw new Error("Configure o secret KAPSO_API_KEY");
    var targets = {};
    var states = ["running", "waiting"];
    for (var s = 0; s < states.length; s++) {
      var cursor = "";
      for (var page = 0; page < 5; page++) {
        var path = "/whatsapp/conversations/" + encodeURIComponent(conversation.id);
        path += "/flow_executions?status=" + states[s] + "&limit=100";
        if (cursor) path += "&after=" + encodeURIComponent(cursor);
        var listing = await api(path);
        if (!Array.isArray(listing.data)) throw new Error("Lista de execucoes invalida");
        for (var i = 0; i < listing.data.length; i++) {
          var item = listing.data[i];
          if ((item.workflow || {}).id === target && states.indexOf(item.status) >= 0
              && typeof item.id === "string" && item.id.length === 36
              && Date.parse(item.started_at) <= sentAt + 999) targets[item.id] = true;
        }
        var paging = listing.paging || {};
        if (!paging.next) break;
        var next = (paging.cursors || {}).after;
        if (!next || next === cursor || page === 4) throw new Error("Paginacao incompleta");
        cursor = next;
      }
    }
    var ids = Object.keys(targets);
    var paused = [];
    for (var j = 0; j < ids.length; j++) {
      var id = ids[j];
      var current = await api("/workflow_executions/" + encodeURIComponent(id));
      var run = current.data || {};
      if ((run.workflow || {}).id !== target || run.whatsapp_conversation_id !== conversation.id
          || states.indexOf(run.status) < 0) continue;
      await api("/workflow_executions/" + encodeURIComponent(id), {
        workflow_execution: { status: "handoff" }
      });
      paused.push(id);
    }
    return result({ vars: { pausa_humano: {
      status: paused.length ? "pausado" : "sem_execucao_ativa", execucoes: paused
    } } });
  } catch (error) {
    return result({ error: String(error.message || error) }, 500);
  }
}
