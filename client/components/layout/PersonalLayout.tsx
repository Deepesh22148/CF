import React from "react";
import PersonalHeader from "./PersonalHeader";

const PersonalLayout = ({
  user_id,
  children,
}: {
  user_id: string;
  children: React.ReactNode;
}) => {
  return (
    <div className="pt-20 h-screen flex flex-col bg-black overflow-hidden">
      <PersonalHeader user_id={user_id} />

      <main className="flex-1 min-h-0 overflow-hidden">{children}</main>
    </div>
  );
};

export default PersonalLayout;
