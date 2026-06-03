const $ = (id) => document.getElementById(id);
let me = null;

(async function init() {
  if (!requireAuth()) return;
  try {
    me = await api.get("/auth/me");
    $("email").textContent = me.email;
    if (me.team_id == null) return location.replace("team-select.html");
    const team = await api.get(`/teams/${me.team_id}`);
    $("teamName").textContent = team.name + " 팀";
    const members = await api.get(`/teams/${me.team_id}/members`);
    $("count").textContent = `(${members.length})`;
    $("list").innerHTML = members
      .map((m) => {
        const isOwner = m.role === "owner";
        const isMe = m.id === me.id;
        const date = (m.created_at || "").slice(0, 10);
        return `<li class="flex items-center justify-between py-3">
          <div class="flex items-center gap-3">
            <span class="w-9 h-9 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-semibold">
              ${escapeHtml(m.email[0].toUpperCase())}
            </span>
            <div>
              <p class="text-sm font-medium text-slate-800">${escapeHtml(m.email)}${isMe ? " (나)" : ""}</p>
              <p class="text-xs ${isOwner ? "text-amber-600" : "text-slate-400"}">${isOwner ? "★ owner" : "member"}</p>
            </div>
          </div>
          <span class="text-xs text-slate-400">${date}</span>
        </li>`;
      })
      .join("");
  } catch (e) {
    if (e.status === 403) location.replace("team-select.html");
  }
})();

$("leave").addEventListener("click", async () => {
  if (!confirm("팀을 떠나시겠습니까?")) return;
  const msg = $("msg");
  try {
    await api.del(`/teams/${me.team_id}/leave`);
    location.href = "team-select.html";
  } catch (e) {
    msg.textContent =
      e.code === "OWNER_CANNOT_LEAVE"
        ? "팀 소유자는 팀을 떠날 수 없습니다 (소유권 이전은 범위 외)"
        : e.message;
    msg.className = "text-sm mt-3 text-red-600";
    msg.classList.remove("hidden");
  }
});
