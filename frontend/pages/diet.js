import { useEffect, useState } from "react";
import Button from "../components/Button";
import FormInput from "../components/FormInput";
import FormSelect from "../components/FormSelect";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import SectionTitle from "../components/SectionTitle";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

const defaultDietForm = {
  weight: "72",
  goal_type: "finish",
  category: "Open",
  training_days_per_week: "4",
  preparation_weeks: "12",
};

const goalOptions = [
  { label: "Cut", value: "cut" },
  { label: "Maintain", value: "maintain" },
  { label: "Bulk", value: "bulk" },
  { label: "Finish", value: "finish" },
  { label: "Improve", value: "improve" },
  { label: "Compete", value: "compete" },
  { label: "Strength", value: "strength" },
];

function DietMetric({ label, value, subtext }) {
  return (
    <PlanCard>
      <p className="text-sm font-black uppercase tracking-[0.22em] text-white/50">
        {label}
      </p>
      <p className="mt-4 text-4xl font-black uppercase text-volt">{value}</p>
      {subtext && <p className="mt-3 leading-6 text-white/60">{subtext}</p>}
    </PlanCard>
  );
}

function StrategyBlock({ title, children }) {
  return (
    <PlanCard>
      <p className="text-sm font-black uppercase tracking-[0.22em] text-ember">
        {title}
      </p>
      <p className="mt-4 leading-7 text-white/70">{children}</p>
    </PlanCard>
  );
}

export default function DietPage() {
  const { user, isChecking } = useRequireUser();
  const [formData, setFormData] = useState(defaultDietForm);
  const [diet, setDiet] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function loadDietPageData() {
      if (!user || !supabase) {
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const { data: sessionData } = await supabase.auth.getSession();
        const accessToken = sessionData.session?.access_token;

        await Promise.all([
          loadLatestDiet(user.id, accessToken),
          loadLatestProfileAndGoal(),
        ]);
      } finally {
        setIsLoading(false);
      }
    }

    loadDietPageData();
  }, [user]);

  async function loadLatestDiet(userId, accessToken) {
    if (!accessToken) {
      return;
    }

    const response = await fetch(`/api/diet-suggestion/latest/${userId}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (response.status === 404) {
      return;
    }

    const data = await response.json();

    if (!response.ok) {
      setError("Unable to load latest diet suggestion. Run the Stage 8 SQL setup if this is your first time.");
      return;
    }

    setDiet(data.diet);
    localStorage.setItem("hyroxfit_diet", JSON.stringify(data));
  }

  async function loadLatestProfileAndGoal() {
    const [profileResult, goalResult] = await Promise.all([
      supabase
        .from("fitness_profiles")
        .select("weight, training_days_per_week")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from("goals")
        .select("goal_type, category, preparation_weeks")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
    ]);

    setFormData((current) => ({
      ...current,
      ...(profileResult.data?.weight
        ? { weight: String(profileResult.data.weight) }
        : {}),
      ...(profileResult.data?.training_days_per_week
        ? { training_days_per_week: String(profileResult.data.training_days_per_week) }
        : {}),
      ...(goalResult.data?.goal_type
        ? { goal_type: goalResult.data.goal_type }
        : {}),
      ...(goalResult.data?.category ? { category: goalResult.data.category } : {}),
      ...(goalResult.data?.preparation_weeks
        ? { preparation_weeks: String(goalResult.data.preparation_weeks) }
        : {}),
    }));
  }

  function updateField(event) {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  }

  async function generateDietSuggestion() {
    setIsGenerating(true);
    setError("");
    setSuccess("");

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;

      if (!accessToken) {
        throw new Error("Your login session expired. Please log in again.");
      }

      const response = await fetch("/api/diet-suggestion", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          weight: Number(formData.weight),
          goal_type: formData.goal_type,
          category: formData.category,
          training_days_per_week: Number(formData.training_days_per_week),
          preparation_weeks: Number(formData.preparation_weeks),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Unable to generate diet suggestion. Make sure backend is running."
        );
      }

      setDiet(data.diet);
      localStorage.setItem("hyroxfit_diet", JSON.stringify(data));
      setSuccess("Diet suggestion generated and saved successfully.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsGenerating(false);
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
              Sign In To Open Diet Suggestions
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/diet">Login</Button>
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
        <SectionTitle kicker="Diet Engine" title="Fuel Your HYROX Build">
          Rule-based nutrition guidance for calories, protein, hydration, carbs,
          fats, and workout meal timing.
        </SectionTitle>

        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              Nutrition Inputs
            </p>
            <div className="mt-6 grid gap-5 sm:grid-cols-2">
              <FormInput
                label="Weight (kg)"
                name="weight"
                type="number"
                value={formData.weight}
                onChange={updateField}
              />
              <FormSelect
                label="Goal Type"
                name="goal_type"
                value={formData.goal_type}
                onChange={updateField}
                options={goalOptions}
              />
              <FormSelect
                label="Category"
                name="category"
                value={formData.category}
                onChange={updateField}
                options={[
                  { label: "Open", value: "Open" },
                  { label: "Pro", value: "Pro" },
                ]}
              />
              <FormSelect
                label="Training Days"
                name="training_days_per_week"
                value={formData.training_days_per_week}
                onChange={updateField}
                options={[
                  { label: "3 days/week", value: "3" },
                  { label: "4 days/week", value: "4" },
                  { label: "5 days/week", value: "5" },
                  { label: "6 days/week", value: "6" },
                ]}
              />
              <FormInput
                label="Preparation Weeks"
                name="preparation_weeks"
                type="number"
                value={formData.preparation_weeks}
                onChange={updateField}
              />
            </div>

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
              <Button
                type="button"
                onClick={generateDietSuggestion}
                disabled={isGenerating || isLoading}
              >
                {isGenerating ? "Generating..." : "Generate Diet Suggestion"}
              </Button>
              <Button href="/ai-coach?mode=diet" variant="secondary">
                Ask AI Coach To Adjust Diet
              </Button>
              <Button href="/dashboard" variant="secondary">
                Back To Dashboard
              </Button>
            </div>
          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-white/50">
              Latest Diet Suggestion
            </p>
            {isLoading ? (
              <p className="mt-5 text-lg font-bold text-white/70">
                Loading diet data...
              </p>
            ) : diet ? (
              <>
                <h1 className="mt-4 text-5xl font-black uppercase text-white">
                  {diet.daily_calories}
                  <span className="text-2xl text-white/40"> kcal/day</span>
                </h1>
                <p className="mt-5 leading-8 text-white/70">
                  Protein target:{" "}
                  <span className="font-black text-volt">
                    {diet.protein_range}
                  </span>
                </p>
                <p className="mt-3 leading-7 text-white/60">{diet.hydration}</p>
              </>
            ) : (
              <p className="mt-5 leading-7 text-white/70">
                Generate a diet suggestion to see your calories, protein, and
                training fuel guidance.
              </p>
            )}
          </PlanCard>
        </div>

        {diet && (
          <>
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <DietMetric
                label="Calories"
                value={diet.daily_calories}
                subtext="Estimated daily intake"
              />
              <DietMetric
                label="Protein"
                value={diet.protein_range}
                subtext="Daily protein range"
              />
              <DietMetric
                label="Hydration"
                value="3-4 L"
                subtext={diet.hydration}
              />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <StrategyBlock title="Carb Strategy">
                {diet.carb_strategy}
              </StrategyBlock>
              <StrategyBlock title="Fat Strategy">
                {diet.fat_strategy}
              </StrategyBlock>
              <StrategyBlock title="Pre-Workout Meal">
                {diet.pre_workout_meal}
              </StrategyBlock>
              <StrategyBlock title="Post-Workout Meal">
                {diet.post_workout_meal}
              </StrategyBlock>
            </div>

            <PlanCard className="mt-6">
              <h2 className="text-2xl font-black uppercase text-white">
                General Tips
              </h2>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {(diet.general_tips || []).map((tip) => (
                  <p
                    key={tip}
                    className="rounded-lg border border-white/10 bg-black/30 p-4 text-sm font-bold leading-6 text-white/70"
                  >
                    {tip}
                  </p>
                ))}
              </div>
              <p className="mt-5 rounded-lg border border-ember/30 bg-ember/10 p-4 text-sm font-bold leading-6 text-ember">
                {diet.disclaimer}
              </p>
            </PlanCard>
          </>
        )}
      </section>
    </main>
  );
}
