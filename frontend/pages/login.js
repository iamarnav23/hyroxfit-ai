import { useState } from "react";
import { useRouter } from "next/router";
import Button from "../components/Button";
import FormInput from "../components/FormInput";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import { isSupabaseConfigured, supabase } from "../lib/supabaseClient";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const redirectTarget =
    typeof router.query.redirect === "string" ? router.query.redirect : "/form";

  function updateForm(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleLogin(event) {
    event.preventDefault();
    setError("");

    if (!isSupabaseConfigured) {
      setError("Supabase is not configured. Add your frontend environment variables.");
      return;
    }

    setIsLoading(true);

    try {
      const { error: loginError } = await supabase.auth.signInWithPassword({
        email: form.email,
        password: form.password,
      });

      if (loginError) {
        throw loginError;
      }

      router.push(redirectTarget);
    } catch (loginError) {
      setError(loginError.message || "Unable to log in.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <Navbar />
      <section className="mx-auto flex min-h-[calc(100vh-73px)] max-w-5xl items-center px-5 py-12">
        <PlanCard className="mx-auto w-full max-w-xl">
          <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
            Login
          </p>
          <h1 className="mt-3 text-4xl font-black uppercase text-white">
            Return To Your Race Plan
          </h1>
          <p className="mt-4 leading-7 text-white/60">
            Log in to generate and view saved HYROX training plans.
          </p>

          <form onSubmit={handleLogin} className="mt-8 space-y-5">
            <FormInput
              label="Email"
              name="email"
              type="email"
              value={form.email}
              onChange={updateForm}
              placeholder="you@example.com"
            />
            <FormInput
              label="Password"
              name="password"
              type="password"
              value={form.password}
              onChange={updateForm}
              placeholder="Your password"
            />

            {error && (
              <p className="rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm font-bold text-ember">
                {error}
              </p>
            )}

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? "Logging in..." : "Login"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Button href="/signup" variant="secondary">
              Create New Account
            </Button>
          </div>
        </PlanCard>
      </section>
    </main>
  );
}
