import { useState } from "react";
import { useRouter } from "next/router";
import Button from "../components/Button";
import FormInput from "../components/FormInput";
import FormSelect from "../components/FormSelect";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import SectionTitle from "../components/SectionTitle";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

const STATIONS = [
  "1 km run",
  "SkiErg",
  "Sled push",
  "Sled pull",
  "Burpee broad jumps",
  "Rowing",
  "Farmer's carry",
  "Sandbag lunges",
  "Wall balls",
];

const stationPlaceholders = {
  "1 km run": "Example: 1km in 5:30",
  SkiErg: "Example: 1000m in 4:30",
  "Sled push": "Example: 50m at 152kg in 2:30",
  "Sled pull": "Example: 50m at 103kg in 3:00",
  "Burpee broad jumps": "Example: 80m in 5:30",
  Rowing: "Example: 1000m in 4:10",
  "Farmer's carry": "Example: 200m with 2x24kg in 2:00",
  "Sandbag lunges": "Example: 100m with 20kg in 5:00",
  "Wall balls": "Example: 100 reps with 6kg in 6:00",
};

const levelOptions = [
  { label: "Beginner", value: "beginner" },
  { label: "Intermediate", value: "intermediate" },
  { label: "Advanced", value: "advanced" },
];

const difficultyOptions = [
  { label: "Easy", value: "easy" },
  { label: "Medium", value: "medium" },
  { label: "Hard", value: "hard" },
];

const initialStationAssessments = STATIONS.map((station) => ({
  station_name: station,
  level: "beginner",
  current_value: "",
  difficulty: "medium",
}));

function CollapsibleFormSection({
  kicker,
  title,
  description,
  accent = "text-volt",
  isOpen,
  onToggle,
  children,
}) {
  return (
    <section className="panel rounded-lg p-5 md:p-8">
      <button
        type="button"
        onClick={onToggle}
        className="flex min-h-16 w-full flex-col justify-between gap-4 text-left sm:flex-row sm:items-center"
        aria-expanded={isOpen}
      >
        <div>
          <p className={`text-sm font-black uppercase tracking-[0.24em] ${accent}`}>
            {kicker}
          </p>
          <h2 className="mt-2 text-2xl font-black uppercase text-white">
            {title}
          </h2>
          {description && (
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/50">
              {description}
            </p>
          )}
        </div>
        <span className="inline-flex min-h-11 items-center justify-center rounded-lg border border-white/10 bg-white/5 px-4 text-sm font-black uppercase tracking-[0.14em] text-white/70">
          {isOpen ? "Collapse" : "Open"}
        </span>
      </button>

      {isOpen && <div className="mt-6">{children}</div>}
    </section>
  );
}

export default function FormPage() {
  const router = useRouter();
  const { user, isChecking } = useRequireUser();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [openSections, setOpenSections] = useState({
    fitness: true,
    goal: false,
    stations: false,
  });

  const [fitnessProfile, setFitnessProfile] = useState({
    age: "24",
    gender: "male",
    height: "175",
    weight: "72",
    body_type: "athletic",
    training_experience: "beginner",
    training_days_per_week: "4",
    injury_history: "No major injuries",
  });

  const [goal, setGoal] = useState({
    preparation_reason: "Preparing for my first HYROX race",
    category: "Open",
    target_time: "1:30:00",
    preparation_weeks: "12",
    main_weakness: "running",
    goal_type: "finish",
  });

  const [stationAssessments, setStationAssessments] = useState(
    initialStationAssessments
  );

  function updateFitnessProfile(event) {
    const { name, value } = event.target;
    setFitnessProfile((current) => ({ ...current, [name]: value }));
  }

  function updateGoal(event) {
    const { name, value } = event.target;
    setGoal((current) => ({ ...current, [name]: value }));
  }

  function updateStation(index, field, value) {
    setStationAssessments((current) =>
      current.map((station, stationIndex) =>
        stationIndex === index ? { ...station, [field]: value } : station
      )
    );
  }

  function toggleSection(sectionName) {
    setOpenSections((current) => {
      const nextOpenState = !current[sectionName];
      return {
        fitness: false,
        goal: false,
        stations: false,
        [sectionName]: nextOpenState,
      };
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    if (!user) {
      setError("Please log in before generating a plan.");
      setIsLoading(false);
      return;
    }

    const { data: sessionData } = await supabase.auth.getSession();
    const accessToken = sessionData.session?.access_token;

    if (!accessToken) {
      setError("Your login session expired. Please log in again.");
      setIsLoading(false);
      router.push("/login?redirect=/form");
      return;
    }

    const payload = {
      user_id: user.id,
      fitness_profile: {
        ...fitnessProfile,
        age: Number(fitnessProfile.age),
        height: Number(fitnessProfile.height),
        weight: Number(fitnessProfile.weight),
        training_days_per_week: Number(fitnessProfile.training_days_per_week),
      },
      hyrox_assessment: stationAssessments,
      goal: {
        ...goal,
        preparation_weeks: Number(goal.preparation_weeks),
      },
    };

    try {
      const response = await fetch("/api/generate-plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail ||
            errorData.message ||
            "Unable to generate plan. Make sure backend is running."
        );
      }

      const savedPlan = await response.json();
      localStorage.setItem("hyroxfit_plan", JSON.stringify(savedPlan));
      router.push("/plan?fresh=1");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  if (isChecking) {
    return (
      <main className="app-shell">
        <Navbar />
        <section className="mx-auto max-w-4xl px-5 py-20">
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
              Sign In To Save Your Plan
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/form">Login</Button>
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
        <SectionTitle kicker="Plan Builder" title="Build Your HYROX Race Plan">
          Enter your current fitness, goal, and station performance. The backend
          will return a rule-based plan built for your race preparation.
        </SectionTitle>

        <form onSubmit={handleSubmit} className="space-y-5 md:space-y-8">
          <CollapsibleFormSection
            kicker="A. Fitness Profile"
            title="Training Background"
            description="This decides whether the plan starts with foundation, build, or race-specific intensity."
            isOpen={openSections.fitness}
            onToggle={() => toggleSection("fitness")}
          >
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
              <FormInput
                label="Age"
                name="age"
                type="number"
                value={fitnessProfile.age}
                onChange={updateFitnessProfile}
              />
              <FormSelect
                label="Gender"
                name="gender"
                value={fitnessProfile.gender}
                onChange={updateFitnessProfile}
                options={[
                  { label: "Male", value: "male" },
                  { label: "Female", value: "female" },
                  { label: "Other", value: "other" },
                ]}
              />
              <FormInput
                label="Height (cm)"
                name="height"
                type="number"
                value={fitnessProfile.height}
                onChange={updateFitnessProfile}
              />
              <FormInput
                label="Weight (kg)"
                name="weight"
                type="number"
                value={fitnessProfile.weight}
                onChange={updateFitnessProfile}
              />
              <FormSelect
                label="Body Type"
                name="body_type"
                value={fitnessProfile.body_type}
                onChange={updateFitnessProfile}
                options={[
                  { label: "Lean", value: "lean" },
                  { label: "Average", value: "average" },
                  { label: "Athletic", value: "athletic" },
                  { label: "Muscular", value: "muscular" },
                  { label: "Overweight", value: "overweight" },
                  { label: "Higher body fat", value: "higher body fat" },
                ]}
              />
              <FormSelect
                label="Training Experience"
                name="training_experience"
                value={fitnessProfile.training_experience}
                onChange={updateFitnessProfile}
                options={levelOptions}
              />
              <FormSelect
                label="Training Days"
                name="training_days_per_week"
                value={fitnessProfile.training_days_per_week}
                onChange={updateFitnessProfile}
                options={[
                  { label: "3 days/week", value: "3" },
                  { label: "4 days/week", value: "4" },
                  { label: "5 days/week", value: "5" },
                  { label: "6 days/week", value: "6" },
                ]}
              />
              <FormInput
                label="Injury History"
                name="injury_history"
                value={fitnessProfile.injury_history}
                onChange={updateFitnessProfile}
              />
            </div>
          </CollapsibleFormSection>

          <CollapsibleFormSection
            kicker="B. HYROX Goal"
            title="Race Target"
            description="Category and preparation time change the intensity and weekly progression."
            accent="text-electric"
            isOpen={openSections.goal}
            onToggle={() => toggleSection("goal")}
          >
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              <FormInput
                label="Preparation Reason"
                name="preparation_reason"
                value={goal.preparation_reason}
                onChange={updateGoal}
              />
              <FormSelect
                label="Category"
                name="category"
                value={goal.category}
                onChange={updateGoal}
                options={[
                  { label: "Open", value: "Open" },
                  { label: "Pro", value: "Pro" },
                ]}
              />
              <FormInput
                label="Target Time"
                name="target_time"
                value={goal.target_time}
                onChange={updateGoal}
                placeholder="1:30:00"
              />
              <FormInput
                label="Preparation Weeks"
                name="preparation_weeks"
                type="number"
                value={goal.preparation_weeks}
                onChange={updateGoal}
              />
              <FormSelect
                label="Main Weakness"
                name="main_weakness"
                value={goal.main_weakness}
                onChange={updateGoal}
                options={[
                  { label: "Running", value: "running" },
                  ...STATIONS.slice(1).map((station) => ({
                    label: station,
                    value: station,
                  })),
                ]}
              />
              <FormSelect
                label="Goal Type"
                name="goal_type"
                value={goal.goal_type}
                onChange={updateGoal}
                options={[
                  { label: "Finish", value: "finish" },
                  { label: "Improve", value: "improve" },
                  { label: "Compete", value: "compete" },
                ]}
              />
            </div>
          </CollapsibleFormSection>

          <CollapsibleFormSection
            kicker="C. Station Assessment"
            title="HYROX Performance"
            description="Mark hard stations honestly. The planner adds focused work where you need it most."
            accent="text-ember"
            isOpen={openSections.stations}
            onToggle={() => toggleSection("stations")}
          >
            <div className="grid gap-4">
              {stationAssessments.map((station, index) => (
                <div
                  key={station.station_name}
                  className="grid gap-4 rounded-lg border border-white/10 bg-carbon/70 p-4 md:grid-cols-[1fr_1fr_1.4fr_1fr] md:items-end"
                >
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-white/40">
                      Station
                    </p>
                    <p className="mt-2 text-lg font-black text-white">
                      {station.station_name}
                    </p>
                  </div>

                  <FormSelect
                    label="Level"
                    name={`${station.station_name}-level`}
                    value={station.level}
                    onChange={(event) =>
                      updateStation(index, "level", event.target.value)
                    }
                    options={levelOptions}
                  />

                  <FormInput
                    label="Current Value"
                    name={`${station.station_name}-current-value`}
                    value={station.current_value}
                    onChange={(event) =>
                      updateStation(index, "current_value", event.target.value)
                    }
                    placeholder={stationPlaceholders[station.station_name]}
                    helperText="Enter your best current performance or estimated ability."
                  />

                  <FormSelect
                    label="Difficulty"
                    name={`${station.station_name}-difficulty`}
                    value={station.difficulty}
                    onChange={(event) =>
                      updateStation(index, "difficulty", event.target.value)
                    }
                    options={difficultyOptions}
                  />
                </div>
              ))}
            </div>
          </CollapsibleFormSection>

          {error && (
            <div className="rounded-lg border border-ember/40 bg-ember/10 p-4 text-sm font-bold text-ember">
              {error}
            </div>
          )}

          <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:justify-end">
            <Button href="/" variant="secondary">
              Back to Home
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Generating your HYROX plan..." : "Generate Plan"}
            </Button>
          </div>
        </form>
      </section>
    </main>
  );
}
