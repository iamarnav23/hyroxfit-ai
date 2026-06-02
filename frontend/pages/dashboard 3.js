import { useEffect, useState } from "react";
import Button from "../components/Button";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

const scoreStyles = {
  ember: {
    text: "text-ember",
    fill: "bg-ember",
    border: "border-ember/30",
    bg: "bg-ember/10",
  },
  volt: {
    text: "text-volt",
    fill: "bg-volt",
    border: "border-volt/30",
    bg: "bg-volt/10",
  },
  electric: {
    text: "text-electric",
    fill: "bg-electric",
    border: "border-electric/30",
    bg: "bg-electric/10",
  },
};

function clampScore(value) {
  return Math.max(0, Math.min(Number(value) || 0, 100));
}

function ProgressBar({ value, accent = "ember" }) {
  const score = clampScore(value);
  const styles = scoreStyles[accent] || scoreStyles.ember;

  return (
    <div className="h-3 overflow-hidden rounded-full border border-white/10 bg-black/60">
      <div
        className={`h-full rounded-full ${styles.fill} transition-all duration-300`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function ScoreCard({ label, score, description, accent = "ember" }) {
  const styles = scoreStyles[accent] || scoreStyles.ember;

  return (
    <div className={`rounded-lg border ${styles.border} ${styles.bg} p-5`}>
      <p className="text-xs font-black uppercase tracking-[0.18em] text-white/50">
        {label}
      </p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <p className={`text-4xl font-black ${styles.text}`}>{score}</p>
        <span className="pb-1 text-sm font-black text-white/35">/100</span>
      </div>
      <div className="mt-4">
        <ProgressBar value={score} accent={accent} />
      </div>
      <p className="mt-3 text-sm font-bold leading-6 text-white/60">
        {description}
      </p>
    </div>
  );
}

function MiniStat({ label, value, subtext, accent = "volt" }) {
  const styles = scoreStyles[accent] || scoreStyles.volt;

  return (
    <div className="rounded-lg border border-white/10 bg-black/30 p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-white/50">
        {label}
      </p>
      <p className={`mt-2 text-2xl font-black uppercase ${styles.text}`}>
        {value}
      </p>
      {subtext && (
        <p className="mt-2 text-sm font-bold leading-6 text-white/55">
          {subtext}
        </p>
      )}
    </div>
  );
}

function SectionHeading({ eyebrow, title, action }) {
  return (
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
      <div>
        <p className="text-sm font-black uppercase tracking-[0.24em] text-ember">
          {eyebrow}
        </p>
        <h2 className="mt-3 text-3xl font-black uppercase text-white">{title}</h2>
      </div>
      {action}
    </div>
  );
}

function InsightList({ items, emptyText }) {
  if (!items || items.length === 0) {
    return <p className="mt-5 text-sm font-bold text-white/55">{emptyText}</p>;
  }

  return (
    <div className="mt-5 grid gap-3 md:grid-cols-2">
      {items.map((item, index) => (
        <div
          key={`${item.area || item}-${index}`}
          className="rounded-lg border border-white/10 bg-black/30 p-4"
        >
          {item.area ? (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-black uppercase tracking-[0.16em] text-ember">
                  {item.area}
                </span>
                <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[11px] font-black uppercase tracking-[0.12em] text-white/45">
                  {item.type}
                </span>
              </div>
              <p className="mt-3 text-sm font-black leading-6 text-white/80">
                {item.insight}
              </p>
              <p className="mt-2 text-sm font-bold leading-6 text-white/55">
                {item.action}
              </p>
            </>
          ) : (
            <p className="text-sm font-bold leading-6 text-white/70">{item}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function TrendCard({ trend }) {
  const tone =
    trend.direction === "up"
      ? "text-volt border-volt/30 bg-volt/10"
      : trend.direction === "needs_work"
        ? "text-ember border-ember/30 bg-ember/10"
        : "text-electric border-electric/30 bg-electric/10";

  return (
    <div className="rounded-lg border border-white/10 bg-black/30 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-black uppercase tracking-[0.16em] text-white/55">
          {trend.label}
        </p>
        <span className={`rounded-md border px-2 py-1 text-xs font-black ${tone}`}>
          {trend.value}
        </span>
      </div>
      <p className="mt-3 text-sm font-bold leading-6 text-white/65">
        {trend.detail}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { user, isChecking } = useRequireUser();
  const [dashboard, setDashboard] = useState(null);
  const [diet, setDiet] = useState(null);
  const [cardio, setCardio] = useState(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      if (!user || !supabase) {
        return;
      }

      try {
        const { data: sessionData } = await supabase.auth.getSession();
        const accessToken = sessionData.session?.access_token;
        const response = await fetch(`/api/dashboard/${user.id}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.message || "Unable to load dashboard.");
        }

        setDashboard(data);

        const dietResponse = await fetch(`/api/diet-suggestion/latest/${user.id}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (dietResponse.ok) {
          const dietData = await dietResponse.json();
          setDiet(dietData.diet);
        }

        const cardioResponse = await fetch(`/api/cardio/current-plan/${user.id}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (cardioResponse.ok) {
          const cardioData = await cardioResponse.json();
          setCardio(cardioData.plan);
        }
      } catch (dashboardError) {
        setError("Unable to load dashboard. Please try again.");
      } finally {
        setIsLoadingDashboard(false);
      }
    }

    loadDashboard();
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

  if (isLoadingDashboard) {
    return (
      <main className="app-shell">
        <Navbar />
        <section className="mx-auto max-w-5xl px-5 py-20">
          <PlanCard>
            <p className="text-lg font-bold text-white/70">
              Loading dashboard...
            </p>
          </PlanCard>
        </section>
      </main>
    );
  }

  const scores = dashboard?.performance_scores || {};
  const cardioSummary = dashboard?.cardio_lab_summary;
  const cardioPlan = cardioSummary || cardio;
  const aiAdvice = dashboard?.latest_ai_coach_advice;

  return (
    <main className="app-shell">
      <Navbar />
      <section className="mx-auto max-w-7xl px-5 py-12 md:py-16">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              Performance Dashboard
            </p>
            <h1 className="mt-3 text-4xl font-black uppercase text-white md:text-6xl">
              Zone 5 Control Room
            </h1>
            <p className="mt-5 leading-8 text-white/70">
              Logged in as{" "}
              <span className="font-black text-volt">{user?.email}</span>
            </p>
          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-white/50">
              Current Training Phase
            </p>
            {dashboard?.latest_plan_type ? (
              <>
                <h2 className="mt-4 text-3xl font-black uppercase text-white">
                  {dashboard.current_training_phase}
                </h2>
                <p className="mt-3 text-sm font-bold leading-6 text-white/60">
                  {dashboard.latest_plan_type}
                </p>
                {dashboard.current_week_focus && (
                  <p className="mt-4 rounded-lg border border-ember/30 bg-ember/10 p-4 text-sm font-black leading-6 text-white/75">
                    Week {dashboard.current_week_number}:{" "}
                    {dashboard.current_week_focus}
                  </p>
                )}
              </>
            ) : (
              <p className="mt-4 leading-7 text-white/70">
                Generate your first HYROX plan to activate performance tracking.
              </p>
            )}
          </PlanCard>
        </div>

        {error && (
          <div className="mt-6 rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm font-bold text-ember">
            {error}
          </div>
        )}

        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
          <ScoreCard
            label="HYROX Readiness"
            score={scores.hyrox_readiness || 0}
            description="Race readiness from plan completion and station feedback."
          />
          <ScoreCard
            label="Endurance"
            score={scores.endurance || 0}
            accent="electric"
            description="Blend of running, Cardio Lab, and consistency."
          />
          <ScoreCard
            label="Running"
            score={scores.running || 0}
            description="Running readiness from HYROX progress."
          />
          <ScoreCard
            label="Recovery"
            score={scores.recovery || 0}
            accent="volt"
            description="Energy and difficulty pressure from logged sessions."
          />
          <ScoreCard
            label="Consistency"
            score={scores.consistency || 0}
            accent="electric"
            description="How much of the current plan is completed."
          />
          <ScoreCard
            label="Zone Balance"
            score={scores.zone_balance || 0}
            accent="volt"
            description="Cardio Lab balance across easy, tempo, and Zone 5 work."
          />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <PlanCard>
            <SectionHeading
              eyebrow="Coaching Insights"
              title="Adaptive Feedback"
              action={
                <Button href="/ai-coach" variant="secondary">
                  Ask AI Coach
                </Button>
              }
            />
            <InsightList
              items={dashboard?.adaptive_coaching_insights || []}
              emptyText="Log workouts to unlock coaching feedback."
            />
          </PlanCard>

          <PlanCard>
            <SectionHeading eyebrow="Weakness Analysis" title="Priority Limiters" />
            <InsightList
              items={dashboard?.weakness_analysis || []}
              emptyText="No major weakness detected yet."
            />
          </PlanCard>
        </div>

        <PlanCard className="mt-6">
          <SectionHeading eyebrow="Progress Trends" title="Training Direction" />
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {(dashboard?.progress_trends || []).map((trend) => (
              <TrendCard key={trend.label} trend={trend} />
            ))}
          </div>
        </PlanCard>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <PlanCard>
            <SectionHeading eyebrow="HYROX Plan" title="Completion" />
            <div className="mt-5">
              <ProgressBar value={dashboard?.completion_percentage || 0} />
              <p className="mt-3 text-sm font-bold text-white/60">
                {dashboard?.completed_workouts || 0} of{" "}
                {dashboard?.total_workouts || 0} workouts complete
              </p>
            </div>
            <p className="mt-5 text-sm font-bold leading-6 text-white/65">
              {dashboard?.race_readiness_score?.status}
            </p>
          </PlanCard>

          <PlanCard>
            <SectionHeading
              eyebrow="Cardio Lab"
              title="Endurance Summary"
              action={
                <Button href="/cardio-lab" variant="secondary">
                  Open
                </Button>
              }
            />
            {cardioPlan ? (
              <div className="mt-5 grid gap-3">
                <MiniStat
                  label="Current Week"
                  value={`Week ${cardioSummary?.week_number || cardio?.week_number}`}
                  subtext={cardioSummary?.cardio_goal || cardio?.cardio_goal}
                  accent="electric"
                />
                <MiniStat
                  label="Training Mode"
                  value={
                    cardioSummary?.training_mode ||
                    cardio?.preferred_training_mode ||
                    "Mixed"
                  }
                  subtext="Latest saved Cardio Lab focus"
                />
                <MiniStat
                  label="Zone Balance"
                  value={`${scores.zone_balance || 0}/100`}
                  subtext={
                    cardioSummary?.weak_cardio_areas?.length
                      ? cardioSummary.weak_cardio_areas.join(", ")
                      : "No major cardio limiter detected"
                  }
                  accent="volt"
                />
              </div>
            ) : (
              <p className="mt-5 leading-7 text-white/70">
                Build a Cardio Lab plan to track endurance and Zone 5 balance.
              </p>
            )}
          </PlanCard>

          <PlanCard>
            <SectionHeading eyebrow="Recovery" title="This Week" />
            <p className="mt-5 rounded-lg border border-volt/30 bg-volt/10 p-4 text-sm font-black leading-6 text-white/75">
              {dashboard?.weekly_recovery_recommendation}
            </p>
            {diet ? (
              <div className="mt-4 grid gap-3">
                <MiniStat
                  label="Daily Calories"
                  value={diet.daily_calories}
                  subtext="Latest diet engine target"
                />
                <MiniStat
                  label="Protein"
                  value={diet.protein_range}
                  subtext="Daily performance support"
                  accent="electric"
                />
              </div>
            ) : (
              <p className="mt-4 text-sm font-bold leading-6 text-white/55">
                Generate a diet suggestion to add fuel targets here.
              </p>
            )}
          </PlanCard>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <PlanCard>
            <SectionHeading eyebrow="Latest AI Advice" title="Coach Memory" />
            {aiAdvice ? (
              <div className="mt-5 rounded-lg border border-electric/30 bg-electric/10 p-4">
                <p className="text-xs font-black uppercase tracking-[0.18em] text-electric">
                  {aiAdvice.recommendation_type?.replaceAll("_", " ")}
                </p>
                <h3 className="mt-3 text-xl font-black uppercase text-white">
                  {aiAdvice.issue}
                </h3>
                <p className="mt-3 text-sm font-bold leading-6 text-white/70">
                  {aiAdvice.summary}
                </p>
              </div>
            ) : (
              <p className="mt-5 leading-7 text-white/70">
                Ask the AI Coach for a plan or diet adjustment to show the
                latest advice here.
              </p>
            )}
          </PlanCard>

          <PlanCard>
            <SectionHeading eyebrow="Recent Notes" title="Workout Signals" />
            <div className="mt-5 space-y-3">
              {(dashboard?.recent_notes || []).length > 0 ? (
                dashboard.recent_notes.map((note) => (
                  <div
                    key={`${note.workout_id}-${note.created_at}`}
                    className="rounded-lg border border-white/10 bg-black/30 p-4"
                  >
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-volt">
                      {note.workout_id}
                    </p>
                    <p className="mt-2 text-sm font-bold leading-6 text-white/70">
                      {note.notes}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm font-bold text-white/55">
                  Save workout notes to improve dashboard insights.
                </p>
              )}
            </div>
          </PlanCard>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Button href="/plan" variant="secondary">
            View Plan
          </Button>
          <Button href="/cardio-lab" variant="secondary">
            Cardio Lab
          </Button>
          <Button href="/form">HYROX Planner</Button>
        </div>
      </section>
    </main>
  );
}
