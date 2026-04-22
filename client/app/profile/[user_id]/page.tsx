import ProfilePage from "@/pages/ProfilePage";
import { use } from "react";

export default function Page({
  params,
}: {
  params: Promise<{ user_id: string }>;
}) {
  const { user_id } = use(params);
  return (
    <div>
      <ProfilePage user_id={user_id} />
    </div>
  );
}
