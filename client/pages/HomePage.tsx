"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [selected, setSelected] = useState<string>("");
  const router = useRouter();
  const fetchHealth = async () => {
    try {
      const res = await fetch("/api/health");
      console.log(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="h-screen w-full flex items-center justify-center">
      
      <div className="bg-black/50 backdrop-blur-sm p-10 rounded-2xl text-center">
        <h1 className="text-white text-3xl font-bold mb-8">
          CF Project
        </h1>

        <div className="flex gap-6">
          <div
            onClick={() => {
                router.push("/dataset")
            }}
            className={`cursor-pointer px-10 py-6 rounded-xl text-xl font-semibold transition-all duration-30`}
          >
            Dataset Mode
          </div>

          <div
            onClick={() => {
                router.push("/personal/auth")
            }}
            className={`cursor-pointer px-10 py-6 rounded-xl text-xl font-semibold transition-all duration-30`}
          >
            Personal Preference Mode
          </div>
        </div>
      </div>
    </div>
  );
}
