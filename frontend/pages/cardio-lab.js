import { useEffect, useMemo, useState } from "react";
import Button from "../components/Button";
import FormInput from "../components/FormInput";
import FormSelect from "../components/FormSelect";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import SectionTitle from "../components/SectionTitle";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

const defaultProfile = {
  cardio_goal: "Zone 5 / VO2 max improvement",
  preferred_training_mode: "Running",
  experience_level: "beginner",
  training_days_per_week: "4",
  current_1km_time: "6:30",
  current_5km_time: "32:00",
  current_long_run_distance: "5 km",
  resting_heart_rate: "62",
  max_heart_rate: "190",
  available_session_duration: "30-45 min",
  injury_or_limitation: "",
  week_number: "1",
};

const defaultReview = {
  workouts_completed: "0",
  total_workouts: "0",
  average_energy_level: "medium",
  average_difficulty: "medium",
  hardest_session: "",
  updated_1km_time: "",
  updated_5km_time: "",
  notes: "",
};

const cardioGoalOptions = [
  "HYROX endurance",
  "Marathon preparation",
  "General cardiovascular health",
  "Zone 5 / VO2 max improvement",
  "Fat loss endurance",
  "Mixed endurance performance",
].map((value) => ({ label: value, value }));

const modeOptions = ["Running", "Cycling", "Swimming", "Mixed"].map((value) => ({
  label: value,
  value,
}));

const levelOptions = ["beginner", "intermediate", "advanced"].map((value) => ({
  label: value[0].toUpperCase() + value.slice(1),
  value,
}));

function countTrainingDays(plan) {
  return (plan?.days || []).filter((day) => !day.workout_type.includes("Rest"))
    .length;
}

function ZoneBadge({ label, value }) {
  return (
    <div className="rounded-lg border border-volt/20 bg-volt/10 p-4">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-white/50">
        {label.replace("_", " ")}
      </p>
      <p className="mt-2 text-3xl font-black text-volt">{value}</p>
    </div>
  );
}

function ProfileSummaryPill({ label, value }) {
  return (
    <span className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs font-black uppercase tracking-[0.12em] text-white/60">
      <span className="text-volt">{label}:</span> {value}
    </span>
  );
}

export default function CardioLabPage() {
  const { user, isChecking } = useRequireUser();
  const [profile, setProfile] = useState(defaultProfile);
  const [review, setReview] = useState(defaultReview);
  const [plan, setPlan] = useState(null);
  const [cardioPlanId, setCardioPlanId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isGeneratingNext, setIsGeneratingNext] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [adjustment, setAdjustment] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(true);

  const totalWorkouts = useMemo(() => countTrainingDays(plan), [plan]);
  const profileSummary = useMemo(
    () => [
      { label: "Goal", value: profile.cardio_goal },
      { label: "Mode", value: profile.preferred_training_mode },
      { label: "Level", value: profile.experience_level },
      { label: "Days", value: `${profile.training_days_per_week}/week` },
    ],
    [profile]
  );

  useEffect(() => {
    async function loadCurrentPlan() {
      if (!user || !supabase) {
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const accessToken = await getAccessToken();
        const response = await fetch(`/api/cardio/current-plan/${user.id}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (response.status === 404) {
          return;
        }

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.message || "Unable to load Cardio Lab plan.");
        }

        setPlan(data.plan);
        setCardioPlanId(data.cardio_plan_id);
        setIsProfileOpen(false);
        setReview((current) => ({
          ...current,
          total_workouts: String(countTrainingDays(data.plan)),
          workouts_completed: String(countTrainingDays(data.plan)),
        }));
      } catch (loadError) {
        setError("Unable to load Cardio Lab plan. Run the Cardio Lab SQL setup if this is your first time.");
      } finally {
        setIsLoading(false);
      }
    }

    loadCurrentPlan();
  }, [user]);

  useEffect(() => {
    if (totalWorkouts > 0) {
      setReview((current) => ({
        ...current,
        total_workouts: String(totalWorkouts),
        workouts_completed:
          Number(current.workouts_completed) > 0
            ? current.workouts_completed
            : String(totalWorkouts),
      }));
    }
  }, [totalWorkouts]);

  async function getAccessToken() {
    const { data: sessionData } = await supabase.auth.getSession();
    const accessToken = sessionData.session?.access_token;
    if (!accessToken) {
      throw new Error("Your login session expired. Please log in again.");
    }
    return accessToken;
  }

  function updateProfile(event) {
    const { name, value } = event.target;
    setProfile((current) => ({ ...current, [name]: value }));
  }

  function updateReview(event) {
    const { name, value } = event.target;
    setReview((current) => ({ ...current, [name]: value }));
  }

  function buildProfilePayload() {
    return {
      user_id: user.id,
      cardio_goal: profile.cardio_goal,
      preferred_training_mode: profile.preferred_training_mode,
      experience_level: profile.experience_level,
      training_days_per_week: Number(profile.training_days_per_week),
      current_1km_time: profile.current_1km_time || null,
      current_5km_time: profile.current_5km_time || null,
      current_long_run_distance: profile.current_long_run_distance || null,
      resting_heart_rate: profile.resting_heart_rate
        ? Number(profile.resting_heart_rate)
        : null,
      max_heart_rate: profile.max_heart_rate
        ? Number(profile.max_heart_rate)
        : null,
      available_session_duration: profile.available_session_duration,
      injury_or_limitation: profile.injury_or_limitation || "",
      week_number: Number(profile.week_number || 1),
    };
  }

  async function generateWeekPlan() {
    setIsGenerating(true);
    setError("");
    setSuccess("");
    setAdjustment(null);

    try {
      const accessToken = await getAccessToken();
      const response = await fetch("/api/cardio/generate-week-plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(buildProfilePayload()),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Unable to generate Cardio Lab plan. Make sure backend is running."
        );
      }

      setPlan(data.plan);
      setCardioPlanId(data.cardio_plan_id);
      setIsProfileOpen(false);
      setReview((current) => ({
        ...current,
        total_workouts: String(countTrainingDays(data.plan)),
        workouts_completed: String(countTrainingDays(data.plan)),
      }));
      setSuccess(
        data.plan.ai_status === "fallback_used"
          ? "Rule-based Cardio Lab plan generated. AI fallback was used."
          : "Cardio Lab plan generated and saved successfully."
      );
    } catch (generateError) {
      setError(generateError.message);
    } finally {
      setIsGenerating(false);
    }
  }

  async function submitReview() {
    if (!cardioPlanId || !plan) {
      setError("Generate a Cardio Lab plan before submitting a review.");
      return;
    }

    setIsReviewing(true);
    setError("");
    setSuccess("");

    try {
      const accessToken = await getAccessToken();
      const response = await fetch("/api/cardio/weekly-review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          cardio_plan_id: cardioPlanId,
          week_number: plan.week_number,
          workouts_completed: Number(review.workouts_completed),
          total_workouts: Number(review.total_workouts),
          average_energy_level: review.average_energy_level,
          average_difficulty: review.average_difficulty,
          hardest_session: review.hardest_session || "Not specified",
          updated_1km_time: review.updated_1km_time || null,
          updated_5km_time: review.updated_5km_time || null,
          notes: review.notes || "",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Unable to save review.");
      }

      setAdjustment(data.next_week_adjustment);
      setSuccess("Weekly review saved. Next week can now adapt from your feedback.");
    } catch (reviewError) {
      setError(reviewError.message);
    } finally {
      setIsReviewing(false);
    }
  }

  async function generateNextWeek() {
    if (!cardioPlanId) {
      setError("Generate and review a Cardio Lab plan first.");
      return;
    }

    setIsGeneratingNext(true);
    setError("");
    setSuccess("");

    try {
      const accessToken = await getAccessToken();
      const response = await fetch("/api/cardio/generate-next-week-plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          previous_cardio_plan_id: cardioPlanId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Unable to generate next week. Make sure backend is running."
        );
      }

      setPlan(data.plan);
      setCardioPlanId(data.cardio_plan_id);
      setProfile((current) => ({
        ...current,
        week_number: String(data.plan.week_number + 1),
      }));
      setAdjustment(null);
      setSuccess(
        data.plan.ai_status === "fallback_used"
          ? "Next week generated with rule-based fallback."
          : "Next week generated from your feedback."
      );
    } catch (nextError) {
      setError(nextError.message);
    } finally {
      setIsGeneratingNext(false);
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
              Sign In To Open Cardio Lab
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/cardio-lab">Login</Button>
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
        <SectionTitle kicker="Adaptive Endurance" title="Cardio Lab">
          Build your aerobic engine, improve Zone 5 power, and adapt your
          cardio plan every week.
        </SectionTitle>

        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <PlanCard>
            <button
              type="button"
              onClick={() => setIsProfileOpen((current) => !current)}
              aria-expanded={isProfileOpen}
              className="w-full rounded-lg border border-volt/20 bg-black/30 p-5 text-left transition hover:border-volt/50 hover:bg-white/[0.035]"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
                    Cardio Profile
                  </p>
                  <h2 className="mt-2 text-2xl font-black uppercase text-white">
                    Training Details
                  </h2>
                </div>
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-volt/30 bg-volt/10 text-2xl font-black text-volt">
                  {isProfileOpen ? "-" : "+"}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {profileSummary.map((item) => (
                  <ProfileSummaryPill
                    key={item.label}
                    label={item.label}
                    value={item.value}
                  />
                ))}
              </div>
            </button>

            {isProfileOpen && (
              <div className="mt-6 rounded-lg border border-white/10 bg-black/20 p-4 md:p-5">
                <div className="grid gap-5 sm:grid-cols-2">
                  <FormSelect
                    label="Cardio Goal"
                    name="cardio_goal"
                    value={profile.cardio_goal}
                    onChange={updateProfile}
                    options={cardioGoalOptions}
                  />
                  <FormSelect
                    label="Preferred Mode"
                    name="preferred_training_mode"
                    value={profile.preferred_training_mode}
                    onChange={updateProfile}
                    options={modeOptions}
                  />
                  <FormSelect
                    label="Experience"
                    name="experience_level"
                    value={profile.experience_level}
                    onChange={updateProfile}
                    options={levelOptions}
                  />
                  <FormSelect
                    label="Training Days"
                    name="training_days_per_week"
                    value={profile.training_days_per_week}
                    onChange={updateProfile}
                    options={[2, 3, 4, 5, 6].map((day) => ({
                      label: `${day} days/week`,
                      value: String(day),
                    }))}
                  />
                  <FormInput
                    label="Current 1km Time"
                    name="current_1km_time"
                    value={profile.current_1km_time}
                    onChange={updateProfile}
                    required={false}
                    placeholder="Example: 5:30"
                  />
                  <FormInput
                    label="Current 5km Time"
                    name="current_5km_time"
                    value={profile.current_5km_time}
                    onChange={updateProfile}
                    required={false}
                    placeholder="Example: 28:00"
                  />
                  <FormInput
                    label="Long Run Distance"
                    name="current_long_run_distance"
                    value={profile.current_long_run_distance}
                    onChange={updateProfile}
                    required={false}
                    placeholder="Example: 5 km"
                  />
                  <FormInput
                    label="Resting HR"
                    name="resting_heart_rate"
                    value={profile.resting_heart_rate}
                    onChange={updateProfile}
                    required={false}
                    type="number"
                  />
                  <FormInput
                    label="Max HR"
                    name="max_heart_rate"
                    value={profile.max_heart_rate}
                    onChange={updateProfile}
                    required={false}
                    type="number"
                  />
                  <FormSelect
                    label="Session Duration"
                    name="available_session_duration"
                    value={profile.available_session_duration}
                    onChange={updateProfile}
                    options={[
                      { label: "30-45 min", value: "30-45 min" },
                      { label: "45-60 min", value: "45-60 min" },
                      { label: "60+ min", value: "60+ min" },
                    ]}
                  />
                  <FormInput
                    label="Week Number"
                    name="week_number"
                    value={profile.week_number}
                    onChange={updateProfile}
                    type="number"
                  />
                  <FormInput
                    label="Injury / Limitation"
                    name="injury_or_limitation"
                    value={profile.injury_or_limitation}
                    onChange={updateProfile}
                    required={false}
                    placeholder="Optional"
                  />
                </div>

                <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                  <Button
                    type="button"
                    onClick={generateWeekPlan}
                    disabled={isGenerating || isLoading}
                  >
                    {isGenerating
                      ? "Building your cardio plan..."
                      : "Generate Week Plan"}
                  </Button>
                  <Button href="/dashboard" variant="secondary">
                    Back To Dashboard
                  </Button>
                </div>
              </div>
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

          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-white/50">
              Current Cardio Plan
            </p>
            {isLoading ? (
              <p className="mt-5 text-lg font-bold text-white/70">
                Loading Cardio Lab...
              </p>
            ) : plan ? (
              <>
                <h1 className="mt-4 text-4xl font-black uppercase text-white md:text-5xl">
                  Week {plan.week_number}
                </h1>
                <p className="mt-4 leading-8 text-white/70">
                  {plan.week_summary}
                </p>
                <p className="mt-4 inline-flex rounded-lg border border-volt/30 bg-volt/10 px-4 py-2 text-sm font-black uppercase tracking-[0.16em] text-volt">
                  {plan.ai_status === "personalized"
                    ? "AI Personalized"
                    : "Rule-Based Fallback"}
                </p>
                <p className="mt-5 leading-7 text-white/60">
                  {plan.plan_reasoning}
                </p>
              </>
            ) : (
              <p className="mt-5 leading-7 text-white/70">
                Generate your first Cardio Lab plan to see zones, intervals,
                coaching tips, and weekly adaptation.
              </p>
            )}
          </PlanCard>
        </div>

        {plan && (
          <>
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
              {Object.entries(plan.zone_distribution || {}).map(([label, value]) => (
                <ZoneBadge key={label} label={label} value={value} />
              ))}
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-5">
              {(plan.training_zones || []).map((zone) => (
                <div
                  key={zone.zone}
                  className="rounded-lg border border-white/10 bg-black/30 p-4"
                >
                  <p className="text-sm font-black uppercase tracking-[0.18em] text-volt">
                    {zone.zone}
                  </p>
                  <p className="mt-2 text-sm font-bold text-white/75">
                    {zone.purpose}
                  </p>
                  <p className="mt-2 text-xs font-bold text-white/50">
                    {zone.percent_max_hr} | RPE {zone.rpe}
                  </p>
                  {zone.heart_rate_range && (
                    <p className="mt-2 text-xs font-black text-electric">
                      {zone.heart_rate_range}
                    </p>
                  )}
                </div>
              ))}
            </div>

            <section className="mt-8 grid gap-4 lg:grid-cols-2">
              {(plan.days || []).map((day) => (
                <PlanCard key={`${day.day}-${day.workout_title}`}>
                  <div className="flex flex-col justify-between gap-3 sm:flex-row">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.22em] text-volt">
                        {day.day} | {day.zone}
                      </p>
                      <h3 className="mt-2 text-xl font-black uppercase text-white md:text-2xl">
                        {day.workout_title}
                      </h3>
                    </div>
                    <span className="h-fit rounded-lg border border-ember/20 bg-ember/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-ember">
                      {day.duration}
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-white/60">
                      {day.training_mode}
                    </span>
                    <span className="rounded-lg border border-volt/20 bg-volt/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-volt">
                      RPE {day.rpe}
                    </span>
                    <span className="rounded-lg border border-electric/20 bg-electric/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-electric">
                      {day.intensity}
                    </span>
                  </div>

                  <p className="mt-4 leading-7 text-white/70">{day.details}</p>
                  <p className="mt-4 rounded-lg border border-white/10 bg-black/30 p-4 text-sm font-bold leading-6 text-white/70">
                    {day.coaching_tip}
                  </p>
                  <p className="mt-3 text-sm font-bold leading-6 text-ember">
                    {day.safety_note}
                  </p>
                </PlanCard>
              ))}
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <PlanCard>
                <p className="text-sm font-black uppercase tracking-[0.24em] text-ember">
                  Progression Advice
                </p>
                <p className="mt-4 leading-7 text-white/70">
                  {plan.progression_advice}
                </p>
              </PlanCard>
              <PlanCard>
                <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
                  Recovery Advice
                </p>
                <p className="mt-4 leading-7 text-white/70">
                  {plan.recovery_advice}
                </p>
                <p className="mt-4 rounded-lg border border-ember/30 bg-ember/10 p-4 text-sm font-bold leading-6 text-ember">
                  {plan.safety_disclaimer}
                </p>
              </PlanCard>
            </div>

            <PlanCard className="mt-6">
              <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
                <div>
                  <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
                    Weekly Review
                  </p>
                  <h2 className="mt-3 text-3xl font-black uppercase text-white">
                    Adapt Next Week
                  </h2>
                </div>
                <Button
                  type="button"
                  onClick={generateNextWeek}
                  disabled={isGeneratingNext || !cardioPlanId}
                  variant="secondary"
                >
                  {isGeneratingNext
                    ? "Generating next week..."
                    : "Generate Next Week Plan"}
                </Button>
              </div>

              <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <FormInput
                  label="Workouts Completed"
                  name="workouts_completed"
                  value={review.workouts_completed}
                  onChange={updateReview}
                  type="number"
                />
                <FormInput
                  label="Total Workouts"
                  name="total_workouts"
                  value={review.total_workouts}
                  onChange={updateReview}
                  type="number"
                />
                <FormSelect
                  label="Average Energy"
                  name="average_energy_level"
                  value={review.average_energy_level}
                  onChange={updateReview}
                  options={["low", "medium", "high"].map((value) => ({
                    label: value,
                    value,
                  }))}
                />
                <FormSelect
                  label="Average Difficulty"
                  name="average_difficulty"
                  value={review.average_difficulty}
                  onChange={updateReview}
                  options={["easy", "medium", "hard"].map((value) => ({
                    label: value,
                    value,
                  }))}
                />
                <FormInput
                  label="Hardest Session"
                  name="hardest_session"
                  value={review.hardest_session}
                  onChange={updateReview}
                  placeholder="Example: Monday Zone 5"
                />
                <FormInput
                  label="Updated 1km Time"
                  name="updated_1km_time"
                  value={review.updated_1km_time}
                  onChange={updateReview}
                  required={false}
                />
                <FormInput
                  label="Updated 5km Time"
                  name="updated_5km_time"
                  value={review.updated_5km_time}
                  onChange={updateReview}
                  required={false}
                />
                <FormInput
                  label="Notes"
                  name="notes"
                  value={review.notes}
                  onChange={updateReview}
                  required={false}
                  placeholder="Energy, soreness, pain, wins..."
                />
              </div>

              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Button
                  type="button"
                  onClick={submitReview}
                  disabled={isReviewing || !cardioPlanId}
                >
                  {isReviewing ? "Saving review..." : "Submit Review"}
                </Button>
              </div>

              {adjustment && (
                <div className="mt-5 rounded-lg border border-electric/30 bg-electric/10 p-4">
                  <p className="text-sm font-black uppercase tracking-[0.18em] text-electric">
                    Next Week Adjustment
                  </p>
                  <p className="mt-2 leading-7 text-white/75">
                    {adjustment.message}
                  </p>
                </div>
              )}
            </PlanCard>
          </>
        )}
      </section>
    </main>
  );
}
