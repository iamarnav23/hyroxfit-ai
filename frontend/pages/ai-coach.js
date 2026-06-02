import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Button from "../components/Button";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import SectionTitle from "../components/SectionTitle";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

const modes = [
  { label: "Plan Adjustment", value: "plan_adjustment" },
  { label: "Diet Adjustment", value: "diet_adjustment" },
  { label: "Plan Explanation", value: "plan_explanation" },
];

const examplePrompts = [
  { text: "Make my plan easier", mode: "plan_adjustment" },
  { text: "I missed 3 workouts this week", mode: "plan_adjustment" },
  { text: "I have knee pain during running", mode: "plan_adjustment" },
  { text: "I do not have access to sled equipment", mode: "plan_adjustment" },
  { text: "I feel low energy during workouts", mode: "diet_adjustment" },
  { text: "I want to focus more on wall balls", mode: "plan_adjustment" },
];

function getInitialMode(queryMode) {
  if (queryMode === "diet") {
    return "diet_adjustment";
  }
  if (queryMode === "explain") {
    return "plan_explanation";
  }
  return "plan_adjustment";
}

function getLoadingMessage(mode) {
  if (mode === "plan_explanation") {
    return "Personalizing your strategy...";
  }
  if (mode === "diet_adjustment") {
    return "Preparing safe adjustments...";
  }
  return "AI Coach is analyzing your plan...";
}

function getErrorMessage(data) {
  if (data?.detail?.error) {
    return data.detail.error;
  }
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  return data?.message || "AI coach is temporarily unavailable.";
}

function ResponseSection({ title, children }) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/30 p-5">
      <p className="text-sm font-black uppercase tracking-[0.2em] text-ember">
        {title}
      </p>
      <div className="mt-3 leading-7 text-white/75">{children}</div>
    </div>
  );
}

export default function AICoachPage() {
  const router = useRouter();
  const { user, isChecking } = useRequireUser();
  const [mode, setMode] = useState("plan_adjustment");
  const [userMessage, setUserMessage] = useState("");
  const [planInfo, setPlanInfo] = useState(null);
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setMode(getInitialMode(router.query.mode));
  }, [router.query.mode]);

  useEffect(() => {
    async function loadLatestPlan() {
      if (!user || !supabase) {
        return;
      }

      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;

      if (!accessToken) {
        return;
      }

      const latestPlanResponse = await fetch(`/api/plans/latest/${user.id}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (latestPlanResponse.ok) {
        const latestPlan = await latestPlanResponse.json();
        setPlanInfo(latestPlan);
      }
    }

    loadLatestPlan();
  }, [user]);

  function useExample(prompt) {
    setMode(prompt.mode);
    setUserMessage(prompt.text);
    setResponse(null);
    setError("");
    setSuccess("");
  }

  async function askCoach() {
    setIsLoading(true);
    setError("");
    setSuccess("");
    setResponse(null);

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;

      if (!accessToken) {
        throw new Error("Your login session expired. Please log in again.");
      }

      if (mode !== "diet_adjustment" && !planInfo?.plan_id) {
        throw new Error("Generate a plan first so AI Coach has a plan to review.");
      }

      if (mode !== "plan_explanation" && !userMessage.trim()) {
        throw new Error("Tell AI Coach what you want help with.");
      }

      const endpoint =
        mode === "plan_explanation"
          ? "/api/ai/personalize-plan"
          : mode === "diet_adjustment"
            ? "/api/ai/adjust-diet"
            : "/api/ai/adjust-plan";

      const body =
        mode === "plan_explanation"
          ? { user_id: user.id, plan_id: planInfo.plan_id }
          : mode === "diet_adjustment"
            ? { user_id: user.id, user_message: userMessage }
            : {
                user_id: user.id,
                plan_id: planInfo.plan_id,
                user_message: userMessage,
              };

      const coachResponse = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(body),
      });

      const data = await coachResponse.json();

      if (!coachResponse.ok) {
        throw new Error(getErrorMessage(data));
      }

      setResponse(data);
      setSuccess("AI recommendation saved for review.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function applyChanges() {
    if (!response?.ai_recommendation_id || !planInfo?.plan_id) {
      return;
    }

    setIsApplying(true);
    setError("");

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;
      const applyResponse = await fetch("/api/ai/apply-plan-changes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          plan_id: planInfo.plan_id,
          ai_recommendation_id: response.ai_recommendation_id,
        }),
      });

      const data = await applyResponse.json();

      if (!applyResponse.ok) {
        throw new Error(getErrorMessage(data));
      }

      localStorage.setItem(
        "hyroxfit_plan",
        JSON.stringify({
          message: data.message,
          plan_id: data.plan_id,
          plan: data.plan,
        })
      );
      setSuccess("AI changes applied as a new plan version.");
      router.push("/plan");
    } catch (applyError) {
      setError(applyError.message);
    } finally {
      setIsApplying(false);
    }
  }

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
              Sign In To Use AI Coach
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/ai-coach">Login</Button>
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
        <SectionTitle kicker="AI Coach" title="Tune Your HYROX Strategy">
          Ask for safer plan changes, diet adjustments, or a coach-style
          explanation of why your plan fits.
        </SectionTitle>

        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              Coach Mode
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              {modes.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setMode(item.value)}
                  className={`rounded-lg border px-4 py-3 text-left text-sm font-black uppercase tracking-[0.14em] transition ${
                    mode === item.value
                      ? "border-volt/50 bg-volt text-carbon"
                      : "border-white/10 bg-black/30 text-white/70 hover:border-volt/30"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <p className="mt-6 text-sm font-black uppercase tracking-[0.22em] text-white/50">
              Example Prompts
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              {examplePrompts.map((prompt) => (
                <button
                  key={prompt.text}
                  type="button"
                  onClick={() => useExample(prompt)}
                  className="min-h-11 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-xs font-bold leading-5 text-white/70 transition hover:border-ember/40 hover:text-white"
                >
                  {prompt.text}
                </button>
              ))}
            </div>

            <div className="mt-6 rounded-lg border border-white/10 bg-black/30 p-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-white/50">
                Latest Plan
              </p>
              <p className="mt-2 font-bold leading-6 text-white/75">
                {planInfo?.plan?.plan_type || "No saved plan loaded yet"}
              </p>
            </div>
          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-ember">
              Ask The Coach
            </p>
            {mode === "plan_explanation" ? (
              <p className="mt-4 leading-7 text-white/70">
                Plan explanation uses your latest saved plan, profile, goal,
                progress, and diet context. No message is needed.
              </p>
            ) : (
              <label className="mt-5 block">
                <span className="mb-2 block text-sm font-bold uppercase tracking-[0.16em] text-white/60">
                  Your Message
                </span>
                <textarea
                  className="input-field min-h-40 resize-y"
                  value={userMessage}
                  onChange={(event) => setUserMessage(event.target.value)}
                  placeholder="Example: This plan is too hard and my knees hurt during running."
                />
              </label>
            )}

            {error && (
              <div className="mt-5 rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm font-bold text-ember">
                {error}
              </div>
            )}

            {success && (
              <div className="mt-5 rounded-lg border border-green-500/40 bg-green-500/10 p-4 text-sm font-bold text-green-300">
                {success}
              </div>
            )}

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Button type="button" onClick={askCoach} disabled={isLoading}>
                {isLoading ? getLoadingMessage(mode) : "Ask AI Coach"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setResponse(null);
                  setSuccess("");
                  setError("");
                }}
              >
                Dismiss
              </Button>
            </div>
          </PlanCard>
        </div>

        {response && (
          <PlanCard className="mt-6">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
                  AI Recommendation
                </p>
                <h2 className="mt-3 text-3xl font-black uppercase text-white">
                  {response.recommendation_type.replace("_", " ")}
                </h2>
              </div>
              <span className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-black uppercase tracking-[0.14em] text-white/60">
                Review First
              </span>
            </div>

            <div className="mt-6 grid gap-4">
              <CoachResult response={response} />
            </div>

            {response.recommendation_type === "plan_adjustment" &&
              response.result?.requires_user_approval && (
                <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
                  <Button
                    type="button"
                    onClick={applyChanges}
                    disabled={isApplying}
                  >
                    {isApplying ? "Applying Changes..." : "Apply Changes"}
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setResponse(null)}
                  >
                    Dismiss
                  </Button>
                </div>
              )}
          </PlanCard>
        )}
      </section>
    </main>
  );
}

function CoachResult({ response }) {
  const result = response.result || {};

  if (response.recommendation_type === "plan_personalization") {
    return (
      <>
        <ResponseSection title="Personalized Summary">
          {result.personalized_summary}
        </ResponseSection>
        <ResponseSection title="Why It Fits">
          {result.why_this_plan_fits}
        </ResponseSection>
        <ResponseSection title="Weekly Notes">
          <div className="grid gap-3 md:grid-cols-2">
            {(result.weekly_coaching_notes || []).map((item) => (
              <div
                key={item.week}
                className="rounded-lg border border-white/10 bg-carbon/70 p-4"
              >
                <p className="text-sm font-black uppercase tracking-[0.16em] text-volt">
                  Week {item.week}
                </p>
                <p className="mt-2 text-white/70">{item.note}</p>
              </div>
            ))}
          </div>
        </ResponseSection>
        <ResponseSection title="Weakness Strategy">
          <div className="grid gap-3 md:grid-cols-2">
            {(result.weakness_strategy || []).map((item) => (
              <div
                key={`${item.weakness}-${item.strategy}`}
                className="rounded-lg border border-white/10 bg-carbon/70 p-4"
              >
                <p className="text-sm font-black uppercase tracking-[0.16em] text-ember">
                  {item.weakness}
                </p>
                <p className="mt-2 text-white/70">{item.strategy}</p>
              </div>
            ))}
          </div>
        </ResponseSection>
        <ResponseSection title="Recovery Advice">
          {result.recovery_advice}
        </ResponseSection>
        <ResponseSection title="Safety Note">{result.safety_note}</ResponseSection>
      </>
    );
  }

  if (response.recommendation_type === "diet_adjustment") {
    return (
      <>
        <ResponseSection title="Issue Detected">
          {result.issue_detected}
        </ResponseSection>
        <ResponseSection title="Coach Response">
          {result.coach_response}
        </ResponseSection>
        <ResponseSection title="Diet Adjustments">
          <div className="grid gap-3 md:grid-cols-2">
            {(result.diet_adjustments || []).map((item) => (
              <div
                key={`${item.adjustment_type}-${item.details}`}
                className="rounded-lg border border-white/10 bg-carbon/70 p-4"
              >
                <p className="text-sm font-black uppercase tracking-[0.16em] text-volt">
                  {item.adjustment_type}
                </p>
                <p className="mt-2 text-white/70">{item.details}</p>
              </div>
            ))}
          </div>
        </ResponseSection>
        <ResponseSection title="Calories">
          <span className="font-black text-volt">
            {result.calorie_adjustment?.suggested_change}
          </span>
          <p className="mt-2">{result.calorie_adjustment?.reason}</p>
        </ResponseSection>
        <ResponseSection title="Meal Timing">
          {result.meal_timing_advice}
        </ResponseSection>
        <ResponseSection title="Hydration">
          {result.hydration_advice}
        </ResponseSection>
        <ResponseSection title="Safety Note">{result.safety_note}</ResponseSection>
      </>
    );
  }

  return (
    <>
      <ResponseSection title="Issue Detected">
        {result.issue_detected}
      </ResponseSection>
      <ResponseSection title="Coach Response">
        {result.coach_response}
      </ResponseSection>
      <ResponseSection title="Recommended Changes">
        <div className="grid gap-3 md:grid-cols-2">
          {(result.recommended_changes || []).map((item) => (
            <div
              key={`${item.change_type}-${item.details}`}
              className="rounded-lg border border-white/10 bg-carbon/70 p-4"
            >
              <p className="text-sm font-black uppercase tracking-[0.16em] text-volt">
                {item.change_type}
              </p>
              <p className="mt-2 font-bold text-white/80">{item.reason}</p>
              <p className="mt-2 text-white/70">{item.details}</p>
            </div>
          ))}
        </div>
      </ResponseSection>
      <ResponseSection title="Updated Plan Preview">
        <div className="space-y-3">
          {(result.updated_plan_preview?.modified_workouts || []).map((item) => (
            <div
              key={item.workout_id}
              className="rounded-lg border border-white/10 bg-carbon/70 p-4"
            >
              <p className="text-xs font-black uppercase tracking-[0.16em] text-ember">
                {item.workout_id}
              </p>
              <h3 className="mt-2 text-xl font-black uppercase text-white">
                {item.new_workout_title}
              </h3>
              <p className="mt-2 text-white/70">{item.new_details}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-lg border border-volt/30 bg-volt/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-volt">
                  {item.new_intensity}
                </span>
                <span className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-white/60">
                  {item.new_duration}
                </span>
              </div>
            </div>
          ))}
        </div>
      </ResponseSection>
      <ResponseSection title="Safety Note">{result.safety_note}</ResponseSection>
    </>
  );
}
