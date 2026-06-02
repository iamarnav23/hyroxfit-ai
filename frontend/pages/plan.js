import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Button from "../components/Button";
import Navbar from "../components/Navbar";
import PlanCard from "../components/PlanCard";
import { supabase } from "../lib/supabaseClient";
import useRequireUser from "../lib/useRequireUser";

function getPlanRecordFromLocalStorage() {
  const savedPlan = localStorage.getItem("hyroxfit_plan");
  if (!savedPlan) {
    return { plan: null, planId: null };
  }

  const parsedPlan = JSON.parse(savedPlan);

  if (parsedPlan.plan) {
    return {
      plan: parsedPlan.plan,
      planId: parsedPlan.plan_id || null,
    };
  }

  return {
    plan: parsedPlan.plan_json || parsedPlan,
    planId: parsedPlan.plan_id || null,
  };
}

function createWorkoutId(weekNumber, dayName) {
  const daySlug = dayName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

  return `week-${weekNumber}-day-${daySlug}`;
}

function getDefaultProgress(workoutId) {
  return {
    workout_id: workoutId,
    completed: false,
    time_taken: "",
    energy_level: "medium",
    difficulty_level: "medium",
    notes: "",
  };
}

function cleanBulletText(text) {
  return text
    .replace(/\s+/g, " ")
    .replace(/^Week \d+ [^.]+? session with [^.]+\.\s*/i, "")
    .replace(/^Week \d+ [^.]+? session\.\s*/i, "")
    .replace(/^Then:\s*/i, "")
    .replace(/^Details:\s*/i, "")
    .trim();
}

function isBaseVolumeBullet(text) {
  const pattern = new RegExp("base " + "(training )?volume", "i");
  return pattern.test(text || "");
}

function splitTextToBullets(text, maxItems = 6) {
  if (!text) {
    return [];
  }

  const bullets = [];
  let remainingText = text;
  const weekMarker = remainingText.match(
    /^(Week \d+ [^.]+?) session with ([^.]+)\.\s*/i
  );

  if (weekMarker) {
    remainingText = remainingText.replace(weekMarker[0], "");
  }

  return [
    ...bullets,
    ...remainingText
      .replace(/\.\s*Then:\s*/g, ". ")
      .replace(/,\s*then\s+/gi, ". ")
      .split(/\.\s+|;\s+/)
      .map(cleanBulletText)
      .filter((item) => !isBaseVolumeBullet(item))
      .filter(Boolean),
  ].slice(0, maxItems);
}

function getWeaknessFocusBullets(plan) {
  return [...new Set(plan.weakness_focus || [])]
    .filter((focus) => !focus.toLowerCase().startsWith("additional focus:"))
    .slice(0, 4);
}

function getPlanSummaryBullets(plan) {
  const workoutDays = plan.weekly_schedule_rules?.workout_days || [];
  const restDays = plan.weekly_schedule_rules?.rest_days || [];
  const weaknessCount = getWeaknessFocusBullets(plan).length;

  return [
    `Phase: ${plan.training_phase}`,
    workoutDays.length > 0
      ? `Workout days: ${workoutDays.join(", ")}`
      : "Workout split generated from your profile",
    restDays.length > 0
      ? `Rest days: ${restDays.join(", ")}`
      : "Recovery days included",
    weaknessCount > 0
      ? `${weaknessCount} weakness focus areas included`
      : "Balanced running, strength, and HYROX skills",
  ];
}

function getWorkoutBullets(day) {
  if (Array.isArray(day.workout_bullets) && day.workout_bullets.length > 0) {
    return day.workout_bullets.map(cleanBulletText).filter(Boolean);
  }

  const bullets = splitTextToBullets(day.details, day.workout_type === "Rest" ? 4 : 7);

  if (day.hyrox_focus && day.workout_type !== "Rest") {
    bullets.push(`HYROX focus: ${day.hyrox_focus}`);
  }

  return bullets;
}

function BulletList({ items, accent = "ember" }) {
  const dotColor = accent === "volt" ? "bg-volt" : "bg-ember";
  const visibleItems = (items || []).filter((item) => !isBaseVolumeBullet(item));

  return (
    <ul className="mt-4 space-y-2">
      {visibleItems.map((item) => (
        <li
          key={item}
          className="flex gap-3 rounded-lg border border-white/10 bg-black/25 px-4 py-3 text-sm font-bold leading-6 text-white/75"
        >
          <span
            className={`mt-2 h-2 w-2 shrink-0 rounded-full ${dotColor}`}
            aria-hidden="true"
          />
          <span className="min-w-0 break-words">{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function PlanPage() {
  const router = useRouter();
  const { user, isChecking } = useRequireUser();
  const [plan, setPlan] = useState(null);
  const [planId, setPlanId] = useState(null);
  const [progressByWorkout, setProgressByWorkout] = useState({});
  const [hasLoaded, setHasLoaded] = useState(false);
  const [saveStatus, setSaveStatus] = useState({});
  const [openWeek, setOpenWeek] = useState(1);

  useEffect(() => {
    async function loadLatestPlanAndProgress() {
      if (!user || !supabase || !router.isReady) {
        return;
      }

      let accessToken = null;

      try {
        const { data: sessionData } = await supabase.auth.getSession();
        accessToken = sessionData.session?.access_token;

        if (router.query.fresh === "1") {
          const localRecord = getPlanRecordFromLocalStorage();
          if (localRecord.plan) {
            setPlan(localRecord.plan);
            setPlanId(localRecord.planId);

            if (localRecord.planId && accessToken) {
              await loadProgress(user.id, localRecord.planId, accessToken);
            }

            setHasLoaded(true);
            return;
          }
        }

        const response = await fetch(`/api/plans/latest/${user.id}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (!response.ok) {
          throw new Error("No saved backend plan found");
        }

        const latestPlan = await response.json();
        setPlan(latestPlan.plan);
        setPlanId(latestPlan.plan_id);
        localStorage.setItem("hyroxfit_plan", JSON.stringify(latestPlan));

        await loadProgress(user.id, latestPlan.plan_id, accessToken);
      } catch (error) {
        const localRecord = getPlanRecordFromLocalStorage();
        setPlan(localRecord.plan);
        setPlanId(localRecord.planId);

        if (localRecord.planId && accessToken) {
          await loadProgress(user.id, localRecord.planId, accessToken);
        }
      } finally {
        setHasLoaded(true);
      }
    }

    loadLatestPlanAndProgress();
  }, [user, router.isReady, router.query.fresh]);

  async function loadProgress(userId, savedPlanId, accessToken) {
    if (!savedPlanId) {
      return;
    }

    const response = await fetch(
      `/api/workout-progress/${userId}/${savedPlanId}`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    if (!response.ok) {
      return;
    }

    const data = await response.json();
    const progressMap = {};

    for (const item of data.progress || []) {
      progressMap[item.workout_id] = item;
    }

    setProgressByWorkout(progressMap);
  }

  function getProgress(workoutId) {
    return progressByWorkout[workoutId] || getDefaultProgress(workoutId);
  }

  function updateProgressField(workoutId, field, value) {
    setProgressByWorkout((current) => ({
      ...current,
      [workoutId]: {
        ...getDefaultProgress(workoutId),
        ...(current[workoutId] || {}),
        [field]: value,
      },
    }));
  }

  function getWeekProgressStats(week) {
    const workoutDays = (week.days || []).filter(
      (day) => day.workout_type !== "Rest"
    );
    const completedWorkouts = workoutDays.filter((day) => {
      const workoutId = createWorkoutId(week.week, day.day);
      return getProgress(workoutId).completed;
    }).length;
    const completionPercentage =
      workoutDays.length > 0
        ? Math.round((completedWorkouts / workoutDays.length) * 100)
        : 0;

    return {
      totalWorkouts: workoutDays.length,
      completedWorkouts,
      completionPercentage,
    };
  }

  async function saveWorkoutProgress(workoutId) {
    if (!user || !supabase || !planId) {
      setSaveStatus({
        [workoutId]: {
          type: "error",
          message: "Unable to save progress because no saved plan was found.",
        },
      });
      return;
    }

    setSaveStatus({
      [workoutId]: {
        type: "loading",
        message: "Saving progress...",
      },
    });

    try {
      const { data: sessionData } = await supabase.auth.getSession();
      const accessToken = sessionData.session?.access_token;
      const progress = getProgress(workoutId);

      const response = await fetch("/api/workout-progress", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          workout_plan_id: planId,
          workout_id: workoutId,
          completed: progress.completed,
          time_taken: progress.time_taken,
          energy_level: progress.energy_level,
          difficulty_level: progress.difficulty_level,
          notes: progress.notes,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Unable to save progress.");
      }

      setProgressByWorkout((current) => ({
        ...current,
        [workoutId]: data.progress,
      }));
      setSaveStatus({
        [workoutId]: {
          type: "success",
          message: "Progress saved successfully.",
        },
      });
    } catch (error) {
      setSaveStatus({
        [workoutId]: {
          type: "error",
          message: "Unable to save progress. Please try again.",
        },
      });
    }
  }

  if (isChecking) {
    return (
      <main className="app-shell">
        <Navbar />
        <div className="mx-auto max-w-7xl px-5 py-20">
          <PlanCard>
            <p className="text-lg font-bold text-white/70">
              Loading your saved plan...
            </p>
          </PlanCard>
        </div>
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
              Sign In To View Saved Plans
            </h1>
            <div className="mt-8">
              <Button href="/login?redirect=/plan">Login</Button>
            </div>
          </PlanCard>
        </section>
      </main>
    );
  }

  if (!hasLoaded) {
    return (
      <main className="app-shell">
        <Navbar />
        <div className="mx-auto max-w-7xl px-5 py-20">
          <PlanCard>
            <p className="text-lg font-bold text-white/70">
              Loading your saved plan...
            </p>
          </PlanCard>
        </div>
      </main>
    );
  }

  if (!plan) {
    return (
      <main className="app-shell">
        <Navbar />
        <section className="mx-auto max-w-4xl px-5 py-20">
          <PlanCard className="text-center">
            <p className="text-sm font-black uppercase tracking-[0.24em] text-volt">
              No Plan Found
            </p>
            <h1 className="mt-4 text-4xl font-black uppercase text-white">
              Generate Your First HYROX Plan
            </h1>
            <p className="mx-auto mt-4 max-w-2xl leading-7 text-white/60">
              Your generated plan will appear here after you submit the planner
              form.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Button href="/form">Generate Plan</Button>
              <Button href="/" variant="secondary">
                Back to Home
              </Button>
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
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.28em] text-volt">
              Generated Training Plan
            </p>
            <h1 className="mt-4 text-4xl font-black uppercase leading-tight text-white md:text-6xl">
              {plan.plan_type}
            </h1>
            <div className="mt-6 inline-flex rounded-lg border border-electric/30 bg-electric/10 px-4 py-2 text-sm font-black uppercase tracking-[0.16em] text-electric">
              {plan.training_phase}
            </div>
          </PlanCard>

          <PlanCard>
            <p className="text-sm font-black uppercase tracking-[0.24em] text-white/50">
              Plan Snapshot
            </p>
            <BulletList items={getPlanSummaryBullets(plan)} accent="volt" />
            {!planId && (
              <p className="mt-4 rounded-lg border border-ember/30 bg-ember/10 p-4 text-sm font-bold text-ember">
                Generate a fresh plan to enable Supabase progress tracking.
              </p>
            )}
          </PlanCard>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <PlanCard>
            <h2 className="text-2xl font-black uppercase text-white">
              Weakness Focus
            </h2>
            <div className="mt-5 space-y-3">
              {getWeaknessFocusBullets(plan).map((focus) => (
                <p
                  key={focus}
                  className="rounded-lg border border-volt/20 bg-volt/10 p-4 text-sm font-bold leading-6 text-white/80"
                >
                  {focus}
                </p>
              ))}
            </div>
          </PlanCard>

          <PlanCard>
            <h2 className="text-2xl font-black uppercase text-white">
              Recommendations
            </h2>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {(plan.recommendations || []).map((recommendation) => (
                <p
                  key={recommendation}
                  className="rounded-lg border border-white/10 bg-carbon/70 p-4 text-sm font-bold leading-6 text-white/70"
                >
                  {recommendation}
                </p>
              ))}
            </div>
          </PlanCard>
        </div>

        <section className="mt-8 space-y-4">
          {(plan.weeks || []).map((week) => {
            const isOpen = openWeek === week.week;
            const weekStats = getWeekProgressStats(week);

            return (
              <PlanCard key={week.week}>
                <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                  <button
                    type="button"
                    onClick={() => setOpenWeek(isOpen ? null : week.week)}
                    aria-expanded={isOpen}
                    aria-controls={`week-${week.week}-workouts`}
                    className="group flex flex-1 flex-col text-left"
                  >
                    <p className="text-sm font-black uppercase tracking-[0.24em] text-ember">
                      Week {week.week}
                    </p>
                    <h2 className="mt-2 text-3xl font-black uppercase text-white transition group-hover:text-ember">
                      {week.focus}
                    </h2>
                  </button>

                  <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-center">
                    <div className="min-w-48">
                      <div className="mb-2 flex items-center justify-between gap-3 text-xs font-black uppercase tracking-[0.14em] text-white/50">
                        <span>
                          {weekStats.completedWorkouts}/{weekStats.totalWorkouts} complete
                        </span>
                        <span>{weekStats.completionPercentage}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-ember transition-all duration-300"
                          style={{ width: `${weekStats.completionPercentage}%` }}
                        />
                      </div>
                    </div>

                    <span className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-center text-sm font-black uppercase tracking-[0.16em] text-white/60">
                      {weekStats.totalWorkouts} workouts
                    </span>

                    <Button
                      type="button"
                      variant={isOpen ? "secondary" : "primary"}
                      onClick={() => setOpenWeek(isOpen ? null : week.week)}
                    >
                      {isOpen ? "Close Week" : "Open Week"}
                    </Button>
                  </div>
                </div>

                {isOpen && (
                  <div
                    id={`week-${week.week}-workouts`}
                    className="mt-6 grid gap-4 lg:grid-cols-2"
                  >
                    {week.days.map((day) => {
                      const workoutId = createWorkoutId(week.week, day.day);
                      const progress = getProgress(workoutId);
                      const status = saveStatus[workoutId];
                      const isRestDay = day.workout_type === "Rest";

                      return (
                        <article
                          key={`${week.week}-${day.day}-${day.workout_title}`}
                          className={`rounded-lg border p-5 transition duration-200 hover:bg-white/[0.04] ${
                            isRestDay
                              ? "border-white/10 bg-black/30"
                              : progress.completed
                                ? "border-green-500/40 bg-green-500/10"
                                : "border-white/10 bg-carbon/70 hover:border-volt/30"
                          }`}
                        >
                          <div className="flex flex-col justify-between gap-3 sm:flex-row">
                            <div>
                              <p className="text-xs font-black uppercase tracking-[0.22em] text-volt">
                                {day.day}
                              </p>
                              <h3 className="mt-2 text-xl font-black uppercase text-white">
                                {day.workout_title}
                              </h3>
                            </div>
                            <div className="flex flex-wrap gap-2 sm:justify-end">
                              {!isRestDay && progress.completed && (
                                <span className="rounded-lg border border-green-500/30 bg-green-500/15 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-green-300">
                                  Completed
                                </span>
                              )}
                              <span className="rounded-lg border border-electric/20 bg-electric/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-electric">
                                {day.duration}
                              </span>
                              <span className="rounded-lg border border-ember/20 bg-ember/10 px-3 py-1 text-xs font-black uppercase tracking-[0.14em] text-ember">
                                {day.intensity}
                              </span>
                            </div>
                          </div>

                          <p className="mt-4 text-sm font-black uppercase tracking-[0.18em] text-white/40">
                            {day.workout_type}
                          </p>
                          <BulletList
                            items={getWorkoutBullets(day)}
                            accent={isRestDay ? "volt" : "ember"}
                          />

                          {!isRestDay && (
                            <>
                              <div className="mt-5 grid gap-4 md:grid-cols-2">
                                <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-black/30 p-4 text-sm font-black uppercase tracking-[0.14em] text-white/70">
                                  <input
                                    type="checkbox"
                                    checked={progress.completed}
                                    onChange={(event) =>
                                      updateProgressField(
                                        workoutId,
                                        "completed",
                                        event.target.checked
                                      )
                                    }
                                    className="h-5 w-5 accent-orange-500"
                                  />
                                  Completed
                                </label>

                                <label>
                                  <span className="mb-2 block text-sm font-bold uppercase tracking-[0.16em] text-white/60">
                                    Time Taken
                                  </span>
                                  <input
                                    className="input-field"
                                    value={progress.time_taken}
                                    onChange={(event) =>
                                      updateProgressField(
                                        workoutId,
                                        "time_taken",
                                        event.target.value
                                      )
                                    }
                                    placeholder="42 minutes"
                                  />
                                </label>

                                <label>
                                  <span className="mb-2 block text-sm font-bold uppercase tracking-[0.16em] text-white/60">
                                    Energy
                                  </span>
                                  <select
                                    className="input-field select-field"
                                    value={progress.energy_level}
                                    onChange={(event) =>
                                      updateProgressField(
                                        workoutId,
                                        "energy_level",
                                        event.target.value
                                      )
                                    }
                                  >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                  </select>
                                </label>

                                <label>
                                  <span className="mb-2 block text-sm font-bold uppercase tracking-[0.16em] text-white/60">
                                    Difficulty
                                  </span>
                                  <select
                                    className="input-field select-field"
                                    value={progress.difficulty_level}
                                    onChange={(event) =>
                                      updateProgressField(
                                        workoutId,
                                        "difficulty_level",
                                        event.target.value
                                      )
                                    }
                                  >
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                  </select>
                                </label>
                              </div>

                              <label className="mt-4 block">
                                <span className="mb-2 block text-sm font-bold uppercase tracking-[0.16em] text-white/60">
                                  Notes
                                </span>
                                <textarea
                                  className="input-field min-h-24 resize-y"
                                  value={progress.notes}
                                  onChange={(event) =>
                                    updateProgressField(
                                      workoutId,
                                      "notes",
                                      event.target.value
                                    )
                                  }
                                  placeholder="Felt strong on running but wall balls were hard"
                                />
                              </label>

                              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                {status && (
                                  <p
                                    className={`text-sm font-bold ${
                                      status.type === "success"
                                        ? "text-green-300"
                                        : status.type === "error"
                                          ? "text-ember"
                                          : "text-white/60"
                                    }`}
                                  >
                                    {status.message}
                                  </p>
                                )}
                                <Button
                                  type="button"
                                  onClick={() => saveWorkoutProgress(workoutId)}
                                  disabled={status?.type === "loading" || !planId}
                                  className="sm:ml-auto"
                                >
                                  Save Progress
                                </Button>
                              </div>
                            </>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}
              </PlanCard>
            );
          })}
        </section>

        <div className="mt-10 flex flex-col justify-end gap-3 sm:flex-row">
          <Button href="/ai-coach?mode=plan" variant="secondary">
            Ask AI Coach To Improve This Plan
          </Button>
          <Button href="/dashboard" variant="secondary">
            View Dashboard
          </Button>
          <Button href="/form">Generate Another Plan</Button>
          <Button href="/" variant="secondary">
            Back to Home
          </Button>
        </div>
      </section>
    </main>
  );
}
