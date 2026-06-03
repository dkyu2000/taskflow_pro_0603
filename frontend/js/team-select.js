const $ = (id) => document.getElementById(id);

(async function init() {
  if (!requireAuth()) return;
  try {
    const me = await api.get("/auth/me");
    $("email").textContent = me.email;
    if (me.team_id != null) {
      location.replace("kanban.html"); // 이미 팀 보유 → 칸반
    }
  } catch {
    /* 401은 api.js가 처리 */
  }
})();

function err(id, msg) {
  const el = $(id);
  el.textContent = msg;
  el.classList.remove("hidden");
}

$("createBtn").addEventListener("click", async () => {
  $("createErr").classList.add("hidden");
  const name = $("teamName").value.trim();
  if (name.length < 1 || name.length > 30) return err("createErr", "팀 이름은 1–30자여야 합니다");
  const btn = $("createBtn");
  btn.disabled = true;
  try {
    const team = await api.post("/teams", { name });
    $("forms").classList.add("hidden");
    $("invite").textContent = team.invite_code;
    $("created").classList.remove("hidden");
    $("copy").addEventListener("click", () => {
      navigator.clipboard?.writeText(team.invite_code);
      $("copy").textContent = "복사됨";
    });
  } catch (e) {
    err("createErr", e.message || "팀 생성 실패");
    btn.disabled = false;
  }
});

$("joinBtn").addEventListener("click", async () => {
  $("joinErr").classList.add("hidden");
  const code = $("code").value.trim().toUpperCase();
  if (!INVITE_RE.test(code)) return err("joinErr", "형식이 올바르지 않습니다 (예: FRNT-2026)");
  const btn = $("joinBtn");
  btn.disabled = true;
  try {
    await api.post("/teams/join", { invite_code: code });
    location.href = "kanban.html";
  } catch (e) {
    if (e.code === "NOT_FOUND") err("joinErr", "해당 초대코드를 찾을 수 없습니다");
    else err("joinErr", e.message || "합류 실패");
    btn.disabled = false;
  }
});
