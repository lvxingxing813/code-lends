export async function login() {
  return fetch("/api/login", { method: "POST" });
}

export async function checkout() {
  return fetch("/api/orders/checkout", { method: "POST" });
}

export async function listUsers() {
  return fetch("/api/users");
}
