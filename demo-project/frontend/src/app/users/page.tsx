import { listUsers } from "../../lib/api";

export default function UsersPage() {
  return <button onClick={listUsers}>用户</button>;
}

