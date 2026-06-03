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

  // 클라이언트 1차 검증 (서버에서도 재검증)
  if (!EMAIL_RE.test(email)) return showError("올바른 이메일 형식이 아닙니다");
  if (password.length < 8) return showError("비밀번호는 8자 이상 입력해주세요");

  const btn = $("submit");
  btn.disabled = true;
  btn.textContent = "처리 중…";
  try {
    const res = await api.post("/auth/signup", { email, password });
    Auth.set(res.token);
    routeAfterAuth(res.user); // 신규 가입 → team_id null → 팀 선택
  } catch (err) {
    showError(err.message || "가입에 실패했습니다");
    btn.disabled = false;
    btn.textContent = "가입하기";
  }
});
