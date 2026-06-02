import { useState } from "react";
import { useRouter } from "next/router";
import Button from "../components/Button";
import FormInput from "../components/FormInput";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import { isSupabaseConfigured, supabase } from "../lib/supabaseClient";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  function updateForm(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSignup(event) {
    event.preventDefault();
    setError("");

    if (!isSupabaseConfigured) {
      setError("Supabase is not configured. Add your frontend environment variables.");
      return;
    }

    setIsLoading(true);

    try {
      const { error: signupError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: {
            name: form.name,
          },
        },
      });

      if (signupError) {
        throw signupError;
      }

      router.push("/form");
    } catch (signupError) {
      setError(signupError.message || "Unable to create account.");
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
            Create Account
          </p>
          <h1 className="mt-3 text-4xl font-black uppercase text-white">
            Start Your HYROX Build
          </h1>
          <p className="mt-4 leading-7 text-white/60">
            Sign up to save your profile, station assessment, goals, and
            generated plans.
          </p>

          <form onSubmit={handleSignup} className="mt-8 space-y-5">
            <FormInput
              label="Name"
              name="name"
              value={form.name}
              onChange={updateForm}
              placeholder="Your name"
            />
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
              placeholder="Minimum 6 characters"
            />

            {error && (
              <p className="rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm font-bold text-ember">
                {error}
              </p>
            )}

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? "Creating account..." : "Sign Up"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Button href="/login" variant="secondary">
              Already Have An Account
            </Button>
          </div>
        </PlanCard>
      </section>
    </main>
  );
}
