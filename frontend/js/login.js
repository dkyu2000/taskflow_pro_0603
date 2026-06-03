const $ = (id) => document.getElementById(id);

function showError(msg) {
  const el = $("error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("error").classList.add("hidden");
  const email = $("email").value.trim();
  const password = $("password").value;

  if (!EMAIL_RE.test(email)) return showError("올바른 이메일 형식이 아닙니다");
  if (!password) return showError("비밀번호를 입력해주세요");

  const btn = $("submit");
  btn.disabled = true;
  btn.textContent = "처리 중…";
  try {
    const res = await api.post("/auth/login", { email, password });
    Auth.set(res.token);
    routeAfterAuth(res.user);
  } catch (err) {
    showError(err.message || "로그인에 실패했습니다");
    btn.disabled = false;
    btn.textContent = "로그인";
  }
});
