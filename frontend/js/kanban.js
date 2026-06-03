const $ = (id) => document.getElementById(id);
const COLS = { TODO: "TODO", DOING: "DOING", DONE: "DONE" };
const COL_STYLE = {
  TODO: "bg-amber-50 text-amber-800",
  DOING: "bg-sky-50 text-sky-800",
  DONE: "bg-emerald-50 text-emerald-800",
};

let me = null,
  team = null,
  members = [],
  tasks = [],
  filter = "",
  current = null; // 모달 대상 태스크

const emailOf = (uid) => {
  const m = members.find((x) => x.id === uid);
  return m ? "@" + m.email.split("@")[0] : "#" + uid;
};

(async function init() {
  if (!requireAuth()) return;
  try {
    me = await api.get("/auth/me");
    $("email").textContent = me.email;
    if (me.team_id == null) return location.replace("team-select.html");
    team = await api.get(`/teams/${me.team_id}`);
    $("teamName").textContent = team.name + " 팀";
    members = await api.get(`/teams/${me.team_id}/members`);
    await loadTasks();
  } catch (e) {
    if (e.status === 403) location.replace("team-select.html");
  }
})();

async function loadTasks() {
  const q = filter ? `?filter=${filter}` : "";
  tasks = await api.get(`/teams/${me.team_id}/tasks${q}`);
  render();
}

document.querySelectorAll(".filter").forEach((b) =>
  b.addEventListener("click", () => {
    filter = b.dataset.filter;
    document.querySelectorAll(".filter").forEach((x) => {
      x.className = "filter px-3 py-1.5 text-sm rounded-lg bg-white border border-slate-300 text-slate-600";
    });
    b.className = "filter px-3 py-1.5 text-sm rounded-lg bg-slate-800 text-white";
    loadTasks();
  })
);

function render() {
  for (const status of Object.keys(COLS)) {
    const col = document.querySelector(`[data-col="${status}"]`);
    const items = tasks.filter((t) => t.status === status);
    col.innerHTML = `
      <div class="rounded-t-xl px-4 py-3 flex items-center justify-between font-semibold ${COL_STYLE[status]}">
        <span>${status} · ${items.length}</span>
        <button class="addBtn text-lg leading-none" data-status="${status}">+</button>
      </div>
      <div class="dropzone bg-white/60 border border-t-0 border-slate-200 rounded-b-xl p-2 min-h-[120px] space-y-2" data-status="${status}">
        ${items.map(cardHtml).join("") || emptyHtml(status)}
      </div>`;
  }
  wire();
}

function cardHtml(t) {
  const badge =
    t.assignee_id == null
      ? `<span class="text-amber-600">⚠ 미할당</span>`
      : `<span class="text-slate-500">${escapeHtml(emailOf(t.assignee_id))}</span>`;
  return `<div draggable="true" data-id="${t.id}"
      class="card bg-white border border-slate-200 rounded-lg p-3 shadow-sm cursor-pointer hover:border-teal-400">
      <p class="font-medium text-slate-800 text-sm mb-1">${escapeHtml(t.title)}</p>
      <p class="text-xs">#${t.id} · ${badge}</p>
    </div>`;
}

function emptyHtml(status) {
  const cta = status === "TODO" ? "+ 첫 태스크 만들기" : "드래그로 이동";
  return `<div class="text-center text-slate-400 text-sm py-8">${cta}</div>`;
}

function wire() {
  // 카드 클릭 → 모달
  document.querySelectorAll(".card").forEach((el) => {
    el.addEventListener("click", () => openModal(Number(el.dataset.id)));
    el.addEventListener("dragstart", (e) => e.dataTransfer.setData("text/plain", el.dataset.id));
  });
  // + 인라인 생성
  document.querySelectorAll(".addBtn").forEach((b) =>
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      openCreate();
    })
  );
  // 드롭존
  document.querySelectorAll(".dropzone").forEach((z) => {
    z.addEventListener("dragover", (e) => {
      e.preventDefault();
      z.classList.add("ring-2", "ring-teal-400");
    });
    z.addEventListener("dragleave", () => z.classList.remove("ring-2", "ring-teal-400"));
    z.addEventListener("drop", async (e) => {
      e.preventDefault();
      z.classList.remove("ring-2", "ring-teal-400");
      const id = Number(e.dataTransfer.getData("text/plain"));
      const status = z.dataset.status;
      const t = tasks.find((x) => x.id === id);
      if (!t || t.status === status) return;
      try {
        await api.patch(`/tasks/${id}/status`, { status });
        await loadTasks();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

// ---- 인라인 생성 (TODO로 생성) ----
function openCreate() {
  const zone = document.querySelector('[data-col="TODO"] .dropzone');
  if (document.getElementById("createRow")) return;
  const opts = assigneeOptions(me.id);
  const row = document.createElement("div");
  row.id = "createRow";
  row.className = "bg-white border-2 border-teal-400 rounded-lg p-3 space-y-2";
  row.innerHTML = `
    <input id="newTitle" maxlength="100" placeholder="새 태스크 제목" autofocus
      class="w-full border border-slate-200 rounded px-2 py-1.5 text-sm focus:outline-none" />
    <div class="flex items-center gap-2">
      <select id="newAssignee" class="border border-slate-200 rounded px-2 py-1 text-sm">${opts}</select>
      <span class="text-xs text-slate-400">Enter 저장 · Esc 취소</span>
    </div>`;
  zone.prepend(row);
  const input = document.getElementById("newTitle");
  input.focus();
  input.addEventListener("keydown", async (e) => {
    if (e.key === "Escape") row.remove();
    if (e.key === "Enter") {
      const title = input.value.trim();
      if (!title) return;
      const a = document.getElementById("newAssignee").value;
      try {
        await api.post(`/teams/${me.team_id}/tasks`, {
          title,
          assignee_id: a === "" ? null : Number(a),
        });
        await loadTasks();
      } catch (err) {
        alert(err.message);
      }
    }
  });
}

function assigneeOptions(selected) {
  const none = `<option value=""${selected == null ? " selected" : ""}>미할당</option>`;
  const list = members
    .map(
      (m) =>
        `<option value="${m.id}"${m.id === selected ? " selected" : ""}>@${escapeHtml(
          m.email.split("@")[0]
        )}</option>`
    )
    .join("");
  return none + list;
}

// ---- 모달 ----
function openModal(id) {
  current = tasks.find((t) => t.id === id);
  if (!current) return;
  $("mId").textContent = "#" + current.id;
  $("mTitle").value = current.title;
  $("mAssignee").innerHTML = assigneeOptions(current.assignee_id);
  $("mMeta").textContent = `생성자 ${emailOf(current.creator_id)} · ${current.created_at?.slice(0, 16).replace("T", " ")}`;
  // 상태 버튼
  $("mStatus").innerHTML = Object.keys(COLS)
    .map(
      (s) =>
        `<button data-s="${s}" class="stbtn px-3 py-1 rounded border text-sm ${
          s === current.status ? "bg-teal-600 text-white border-teal-600" : "border-slate-300 text-slate-600"
        }">${s}</button>`
    )
    .join("");
  $("mStatus")
    .querySelectorAll(".stbtn")
    .forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await api.patch(`/tasks/${current.id}/status`, { status: b.dataset.s });
          await loadTasks();
          current = tasks.find((t) => t.id === current.id);
          openModal(current.id);
        } catch (e) {
          showModalErr(e.message);
        }
      })
    );
  // 삭제 권한: creator 또는 owner
  const canDelete = current.creator_id === me.id || team.owner_id === me.id;
  $("mDelete").classList.toggle("hidden", !canDelete);
  $("mErr").classList.add("hidden");
  $("modal").classList.remove("hidden");
}

function closeModal() {
  $("modal").classList.add("hidden");
  current = null;
}

function showModalErr(msg) {
  $("mErr").textContent = msg;
  $("mErr").classList.remove("hidden");
}

async function saveTask() {
  if (!current) return;
  const title = $("mTitle").value.trim();
  if (!title) return showModalErr("제목을 입력하세요");
  const a = $("mAssignee").value;
  try {
    await api.put(`/tasks/${current.id}`, { title, assignee_id: a === "" ? null : Number(a) });
    closeModal();
    await loadTasks();
  } catch (e) {
    showModalErr(e.message);
  }
}

async function deleteTask() {
  if (!current) return;
  if (!confirm(`'#${current.id} ${current.title}' — 되돌릴 수 없습니다. 삭제할까요?`)) return;
  try {
    await api.del(`/tasks/${current.id}`);
    closeModal();
    await loadTasks();
  } catch (e) {
    showModalErr(e.message);
  }
}
