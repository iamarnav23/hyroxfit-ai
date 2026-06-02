import { useEffect, useState } from "react";
import Button from "../components/Button";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

export default function DashboardPage() {
  const { user, isChecking } = useRequireUser();
  const [latestPlan, setLatestPlan] = useState(null);
  const [isLoadingPlan, setIsLoadingPlan] = useState(true);

  useEffect(() => {
    async function loadDashboardPlan() {
      if (!user || !supabase) {
        return;
      }

      try {
        const { data: sessionData } = await supabase.auth.getSession();
        const response = await fetch(`/api/plans/latest/${user.id}`, {
          headers: {
            Authorization: `Bearer ${sessionData.session?.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error("No saved plan");
        }

        const data = await response.json();
        setLatestPlan(data.plan);
      } catch (error) {
        setLatestPlan(null);
      } finally {
        setIsLoadingPlan(false);
      }
    }

    loadDashboardPlan();
  }, [user]);

  if (isChecking) {
    return (
      <main className="app-shell">
        <Navbar />
        <section className="mx-auto max-w-5xl px-5 py-20">
          <PlanCard>
            <p className="text-lg font-bold text-white/70">
              Checking login session...
            </p>
          </PlanCard>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="app-shell">
        <Navbar />
        <section className="mx-auto max-w-4xl px-5 py-20">
          <PlanCard className="text-center">
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              Login Required
            </p>
            <h1 className="mt-4 text-4xl font-black uppercase text-white">
              Sign In To Open Your Dashboard
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/dashboard">Login</Button>
            </div>
          </PlanCard>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <Navbar />
      <section className="mx-auto max-w-7xl px-5 py-12 md:py-16">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              Dashboard
            </p>
            <h1 className="mt-3 text-4xl font-black uppercase text-white md:text-6xl">
              Your HYROX Control Room
            </h1>
            <p className="mt-5 leading-8 text-white/65">
              Logged in as{" "}
              <span className="font-black text-volt">{user?.email}</span>
            </p>
          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-white/45">
              Latest Saved Plan
            </p>
            {isLoadingPlan ? (
              <p className="mt-4 leading-7 text-white/65">Loading plan...</p>
            ) : latestPlan ? (
              <>
                <h2 className="mt-4 text-3xl font-black uppercase text-white">
                  {latestPlan.plan_type}
                </h2>
                <p className="mt-3 inline-flex rounded-lg border border-volt/30 bg-volt/10 px-4 py-2 text-sm font-black uppercase tracking-[0.16em] text-volt">
                  {latestPlan.training_phase}
                </p>
                <p className="mt-4 leading-7 text-white/65">
                  {latestPlan.summary}
                </p>
              </>
            ) : (
              <p className="mt-4 leading-7 text-white/65">
                No saved plan yet. Generate your first HYROX plan to see it here.
              </p>
            )}
          </PlanCard>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Button href="/plan" variant="secondary">
            View Plan
          </Button>
          <Button href="/form">Generate New Plan</Button>
        </div>
      </section>
    </main>
  );
}
