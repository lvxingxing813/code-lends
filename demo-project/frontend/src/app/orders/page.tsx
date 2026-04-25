import { checkout } from "../../lib/api";

export default function OrdersPage() {
  return <button onClick={checkout}>结算</button>;
}

