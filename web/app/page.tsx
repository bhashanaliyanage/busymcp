"use client";
import { useState } from "react";

export default function Home() {
  const [q, setQ] = useState("");
  const [a, setA] = useState("");
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE!;
  console.log("API Base:", apiBase);

  const ask = async () => {
    const r = await fetch(`${apiBase}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q })
    });
    const j = await r.json();
    setA(j.answer || "No answer");
  };

  /* Test */

  const sendMail = async () => {
    const r = await fetch(`${apiBase}/email/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient, subject, body })
    });
    const j = await r.json();
    alert(j.ok ? "Email sent!" : `Failed: ${j.error}`);
  };

return (
  <main className="min-h-screen flex items-center justify-center bg-[#1d1d1f] p-6">
    <div className="max-w-xl w-full grid gap-6">
      {/* CV Chat Section */}
      <section className="grid gap-3 bg-white/10 p-6 rounded-2xl shadow-lg">
        <h1 className="text-2xl font-semibold text-white">CV Chat</h1>
        <input
          className="border border-gray-400/30 bg-white/5 text-white placeholder-gray-400 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder='Ask: "What role did I have at my last position?"'
        />
        <button
          className="bg-blue-800 text-white p-3 rounded-xl hover:bg-blue-900 transition"
          onClick={ask}
        >
          Ask
        </button>
        <pre className="border border-gray-400/30 p-3 rounded-xl bg-black/40 text-white whitespace-pre-wrap">
          {a}
        </pre>
      </section>

      {/* Send Email Section */}
      <section className="grid gap-3 bg-white/10 p-6 rounded-2xl shadow-lg">
        <h2 className="text-xl font-semibold text-white">Send Email</h2>
        <input
          className="border border-gray-400/30 bg-white/5 text-white placeholder-gray-400 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={recipient}
          onChange={e => setRecipient(e.target.value)}
          placeholder="recipient@example.com"
        />
        <input
          className="border border-gray-400/30 bg-white/5 text-white placeholder-gray-400 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={subject}
          onChange={e => setSubject(e.target.value)}
          placeholder="Subject"
        />
        <textarea
          className="border border-gray-400/30 bg-white/5 text-white placeholder-gray-400 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px]"
          value={body}
          onChange={e => setBody(e.target.value)}
          placeholder="Body"
        />
        <button
          className="bg-blue-800 text-white p-3 rounded-xl hover:bg-blue-900 transition"
          onClick={sendMail}
        >
          Send
        </button>
      </section>
    </div>
  </main>
);

}