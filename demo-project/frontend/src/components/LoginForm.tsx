import { login } from "../lib/api";

export function LoginForm() {
  return <button onClick={login}>登录</button>;
}

