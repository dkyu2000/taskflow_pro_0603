// 공통 API 클라이언트 — JWT 자동 첨부, 401 시 토큰 삭제 후 로그인 redirect
// 프론트엔드는 FastAPI(StaticFiles)와 동일 오리진에서 서빙되며, 모든 API는 /api 프리픽스
const API_BASE = "/api";

const TOKEN_KEY = "taskflow_token";

const Auth = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

class ApiError extends Error {
  constructor(status, code, message, meta) {
    super(message || "요청 실패");
    this.status = status;
    this.code = code;
    this.meta = meta;
  }
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.get();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body != null ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new ApiError(0, "NETWORK", "서버에 연결할 수 없습니다");
  }

  // 401 → 토큰 폐기 후 로그인으로 (직전 URL 저장 X)
  if (res.status === 401) {
    Auth.clear();
    if (!location.pathname.endsWith("login.html")) location.href = "login.html";
    throw new ApiError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다");
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const err = (data && data.error) || {};
    throw new ApiError(res.status, err.code || "ERROR", err.message, err.meta);
  }
  return data;
}

const api = {
  get: (p) => request("GET", p),
  post: (p, b) => request("POST", p, b),
  put: (p, b) => request("PUT", p, b),
  patch: (p, b) => request("PATCH", p, b),
  del: (p) => request("DELETE", p),
};

// ---- 공통 유틸 ----
function requireAuth() {
  if (!Auth.get()) {
    location.href = "login.html";
    return false;
  }
  return true;
}

function logout() {
  Auth.clear();
  location.href = "login.html";
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

function fmtTime(iso) {
  // KST(+09:00) ISO → HH:MM
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const INVITE_RE = /^[A-Z]{4}-[0-9]{4}$/;

// 로그인 후 분기: team_id 유무에 따라 칸반/팀선택
function routeAfterAuth(user) {
  location.href = user && user.team_id != null ? "kanban.html" : "team-select.html";
}
