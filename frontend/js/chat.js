const $ = (id) => document.getElementById(id);
const LIMIT = 1000;
let me = null,
  lastId = 0,
  timer = null;

(async function init() {
  if (!requireAuth()) return;
  try {
    me = await api.get("/auth/me");
    $("email").textContent = me.email;
    if (me.team_id == null) return location.replace("team-select.html");
    const team = await api.get(`/teams/${me.team_id}`);
    $("teamName").textContent = team.name + " 팀";
    const msgs = await api.get(`/teams/${me.team_id}/messages`);
    render(msgs, true);
    timer = setInterval(poll, 5000); // 5초 폴링
  } catch (e) {
    if (e.status === 403) location.replace("team-select.html");
  }
})();

function setStatus(ok) {
  const el = $("status");
  if (ok) {
    el.textContent = "● 5초마다 새로고침";
    el.className = "text-xs text-emerald-600";
  } else {
    el.textContent = "⚠ 연결 끊김 · 재시도 중";
    el.className = "text-xs text-red-600";
  }
}

async function poll() {
  try {
    const msgs = await api.get(`/teams/${me.team_id}/messages?since=${lastId}`);
    setStatus(true);
    if (msgs.length) render(msgs, false); // 빈 배열이면 화면 변화 없음
  } catch (e) {
    if (e.status === 401) return; // api.js가 redirect 처리
    setStatus(false); // 다음 인터벌에 재시도
  }
}

function render(msgs, replace) {
  const list = $("list");
  if (replace) list.innerHTML = "";
  if (replace && msgs.length === 0) {
    list.innerHTML = `<div id="emptyState" class="text-center text-slate-400 py-16">
      💬 아직 대화가 없습니다<br /><span class="text-sm">첫 메시지를 보내 팀원과 대화를 시작하세요</span></div>`;
    return;
  }
  // 빈 상태 placeholder가 떠 있으면 첫 메시지 추가 전에 제거
  if (msgs.length) document.getElementById("emptyState")?.remove();
  for (const m of msgs) {
    if (m.id > lastId) lastId = m.id;
    list.insertAdjacentHTML("beforeend", bubble(m));
  }
  // 본인 메시지 삭제 버튼 연결
  list.querySelectorAll("[data-del]").forEach((b) => {
    if (b.dataset.wired) return;
    b.dataset.wired = "1";
    b.addEventListener("click", async () => {
      try {
        await api.del(`/messages/${b.dataset.del}`);
        document.getElementById(`msg-${b.dataset.del}`)?.remove();
      } catch (e) {
        alert(e.message);
      }
    });
  });
  list.scrollTop = list.scrollHeight;
}

function bubble(m) {
  const mine = m.user_id === me.id;
  const who = escapeHtml(m.user_email.split("@")[0]);
  const time = fmtTime(m.created_at);
  const del = mine
    ? `<button data-del="${m.id}" title="삭제" class="text-xs text-red-400 hover:text-red-600 ml-2">🗑</button>`
    : "";
  return `<div id="msg-${m.id}" class="flex ${mine ? "justify-end" : "justify-start"}">
    <div class="max-w-[75%]">
      <div class="text-xs text-slate-400 mb-0.5 ${mine ? "text-right" : ""}">${mine ? "나" : who} · ${time}${del}</div>
      <div class="px-3 py-2 rounded-2xl text-sm ${
        mine ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-800"
      }">${escapeHtml(m.content)}</div>
    </div>
  </div>`;
}

// 입력 카운터 + 검증
$("input").addEventListener("input", () => {
  const n = $("input").value.length;
  const c = $("counter");
  c.textContent = `${n} / ${LIMIT}`;
  const over = n > LIMIT;
  c.className = over ? "text-xs text-red-600 font-semibold" : "text-xs text-slate-400";
  $("send").disabled = over || n === 0;
});

async function sendMsg() {
  const content = $("input").value.trim();
  $("err").textContent = "";
  if (!content) return;
  if (content.length > LIMIT) return ($("err").textContent = "1000자 이내로 입력하세요");
  $("send").disabled = true;
  try {
    await api.post(`/teams/${me.team_id}/messages`, { content });
    $("input").value = "";
    $("counter").textContent = `0 / ${LIMIT}`;
    await poll();
  } catch (e) {
    $("err").textContent = e.message;
  } finally {
    $("send").disabled = false;
  }
}

$("send").addEventListener("click", sendMsg);
$("input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMsg();
});
