"use client";

import { useRouter } from "next/navigation";
import React from "react";

type User = {
  name: string;
  age: number;
  occupation: string;
  gender: string;
  genres: string[];
};

const PersonalHeader = ({ user_id }: { user_id: string }) => {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [user, setUser] = React.useState<User | null>(null);
  const router = useRouter();

  const fetchPersonalInformation = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch("/api/user/my-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id }),
      });

      const body = await response.json();
      console.log(body);
      if (!response.ok) {
        setError(body.error || "Failed to fetch user");
        return;
      }
      console.log(body.body.data);
      setUser(body.body.data);
    } catch (err) {
      console.error(err);
      setError("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchPersonalInformation();
  }, []);

  return (
    <header className="fixed top-0 left-0 w-full h-16 z-50 bg-slate-900 border-b border-slate-700 text-slate-200">
      <div className="flex items-center justify-between h-full px-6">
        <div className="text-lg text-cyan-400 cursor-pointer"
        onClick={()=> {
          router.push(`/chat/${user_id}`)
        }}
        >Movies, Curated for You</div>

        {/* RIGHT PROFILE */}
        <div className="relative">
          <button
            onClick={() => setOpen(!open)}
            className="bg-slate-800 border border-slate-600 px-4 py-2 rounded-lg text-sm text-slate-100 hover:border-cyan-400 transition"
          >
            {loading ? "Loading..." : user?.name || "Guest"}
          </button>

          {open && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg overflow-hidden">
              {error && (
                <div className="px-4 py-2 text-red-400 text-sm border-b border-slate-700">
                  {error}
                </div>
              )}

              {user && (
                <div className="px-4 py-2 text-slate-200 border-b border-slate-700 text-sm">
                  {user.name}
                </div>
              )}

              <button
                className="w-full text-left px-4 py-2 hover:bg-slate-700 text-sm"
                onClick={() => {
                  router.push(`/profile/${user_id}`);
                }}
              >
                Profile
              </button>

              <button className="w-full text-left px-4 py-2 hover:bg-slate-700 text-red-400 text-sm"
              onClick={() => {
                router.push(`/personal/auth`)
              }}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default PersonalHeader;
