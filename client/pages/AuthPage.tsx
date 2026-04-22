"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";

const occupations = [
  "administrator",
  "artist",
  "doctor",
  "educator",
  "engineer",
  "entertainment",
  "executive",
  "healthcare",
  "homemaker",
  "lawyer",
  "librarian",
  "marketing",
  "none",
  "other",
  "programmer",
  "retired",
  "salesman",
  "scientist",
  "student",
  "technician",
  "writer",
];

const genres = [
  "Action",
  "Adventure",
  "Animation",
  "Children's",
  "Comedy",
  "Crime",
  "Documentary",
  "Drama",
  "Fantasy",
  "Film-Noir",
  "Horror",
  "Musical",
  "Mystery",
  "Romance",
  "Sci-Fi",
  "Thriller",
  "War",
  "Western",
];

const AuthPage = () => {
  const [activeTab, setActiveTab] = useState("signin");
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    password: "",
    confirmPassword: "",
    age: "",
    occupation: "",
    gender: "",
    genres: [] as string[],
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const toggleGenre = (genre: string) => {
    setForm((prev) => ({
      ...prev,
      genres: prev.genres.includes(genre)
        ? prev.genres.filter((g) => g !== genre)
        : [...prev.genres, genre],
    }));
  };

  const handleSignIn = async () => {
    try {
      const response = await fetch("/api/auth/me", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          password: form.password,
        }),
      });

      const body = await response.json();
      if (response.ok) {
        router.push(`/chat/${body.user_id}`)
      }
    } catch (error) {
      console.error(error);
    }
  };

  const handleRegister = async () => {
    if (form.password !== form.confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    try {
      const response = await fetch("/api/user/add-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          password: form.password,
          gender : form.gender,
          age: Number(form.age),
          occupation: form.occupation,
          genres: form.genres,
        }),
      });

      const body = await response.json();
      if (response.ok) console.log(body);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white">
      <div className="w-full max-w-md p-8 rounded-2xl bg-[#0f0f0f] border border-purple-500/30 shadow-[0_0_40px_rgba(168,85,247,0.3)]">
        {/* Tabs */}
        <div className="flex mb-6 border-b border-gray-700">
          <button
            onClick={() => setActiveTab("signin")}
            className={`flex-1 py-2 ${
              activeTab === "signin"
                ? "text-purple-400 border-b-2 border-purple-500"
                : "text-gray-400"
            }`}
          >
            Sign In
          </button>

          <button
            onClick={() => setActiveTab("register")}
            className={`flex-1 py-2 ${
              activeTab === "register"
                ? "text-pink-400 border-b-2 border-pink-500"
                : "text-gray-400"
            }`}
          >
            Register
          </button>
        </div>

        {/* SIGN IN */}
        {activeTab === "signin" ? (
          <div className="space-y-4">
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              type="text"
              placeholder="Username"
              className="w-full px-4 py-2 bg-black border border-purple-500/40 rounded-lg"
            />

            <input
              name="password"
              value={form.password}
              onChange={handleChange}
              type="password"
              placeholder="Password"
              className="w-full px-4 py-2 bg-black border border-purple-500/40 rounded-lg"
            />

            <button
              onClick={handleSignIn}
              className="w-full py-2 bg-purple-600 rounded-lg hover:bg-purple-700"
            >
              Sign In
            </button>
          </div>
        ) : (
          /* REGISTER */
          <div className="space-y-4">
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              type="text"
              placeholder="Username"
              className="w-full px-4 py-2 bg-black border border-pink-500/40 rounded-lg"
            />

            <input
              name="age"
              value={form.age}
              onChange={handleChange}
              type="number"
              placeholder="Age"
              className="w-full px-4 py-2 bg-black border border-pink-500/40 rounded-lg"
            />

            <div>
              <p className="text-sm mb-2 text-gray-400">Gender</p>

              <div className="flex gap-3">
                {["male", "female", "other"].map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setForm({ ...form, gender: g })}
                    className={`px-4 py-1 rounded-full border text-sm ${
                      form.gender === g
                        ? "bg-pink-500 border-pink-500 text-white"
                        : "border-gray-600 text-gray-300 hover:bg-gray-800"
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>

            {/* Occupation Dropdown */}
            <select
              value={form.occupation}
              onChange={(e) => setForm({ ...form, occupation: e.target.value })}
              className="w-full px-4 py-2 bg-black border border-pink-500/40 rounded-lg"
            >
              <option value="">Select occupation</option>
              {occupations.map((occ) => (
                <option key={occ} value={occ}>
                  {occ}
                </option>
              ))}
            </select>

            {/* Genres Multi Select */}
            <div>
              <p className="text-sm mb-2 text-gray-400">Preferred Genres</p>
              <div className="flex flex-wrap gap-2">
                {genres.map((g) => {
                  const selected = form.genres.includes(g);
                  return (
                    <button
                      key={g}
                      onClick={() => toggleGenre(g)}
                      type="button"
                      className={`px-3 py-1 text-sm rounded-full border ${
                        selected
                          ? "bg-pink-500 text-white border-pink-500"
                          : "bg-black border-gray-600 text-gray-300 hover:bg-gray-800"
                      }`}
                    >
                      {g}
                    </button>
                  );
                })}
              </div>
            </div>

            <input
              name="password"
              value={form.password}
              onChange={handleChange}
              type="password"
              placeholder="Password"
              className="w-full px-4 py-2 bg-black border border-pink-500/40 rounded-lg"
            />

            <input
              name="confirmPassword"
              value={form.confirmPassword}
              onChange={handleChange}
              type="password"
              placeholder="Confirm Password"
              className="w-full px-4 py-2 bg-black border border-pink-500/40 rounded-lg"
            />

            <button
              onClick={handleRegister}
              className="w-full py-2 bg-pink-600 rounded-lg hover:bg-pink-700"
            >
              Register
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthPage;
