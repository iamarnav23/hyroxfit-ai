import Button from "../components/Button";
import Navbar from "../components/Navbar";
import SectionTitle from "../components/SectionTitle";
import StatCard from "../components/StatCard";

const steps = [
  {
    title: "Enter Your Profile",
    text: "Add your training background, weekly availability, and injury history.",
  },
  {
    title: "Assess HYROX Stations",
    text: "Rate running, sleds, carries, lunges, rowing, SkiErg, and wall balls.",
  },
  {
    title: "Get Your Plan",
    text: "Receive a race-focused plan matched to your category, timeline, and weakness.",
  },
];

const cardioSteps = [
  {
    title: "Choose Your Cardio Goal",
    text: "Pick Zone 5, marathon prep, cardiovascular health, HYROX endurance, or mixed endurance.",
  },
  {
    title: "Set Your Training Mode",
    text: "Build the week around running, cycling, swimming, or a balanced mixed-cardio split.",
  },
  {
    title: "Adapt Every Week",
    text: "Submit weekly feedback so the next plan can adjust volume, intensity, and recovery.",
  },
];

const features = [
  "Beginner, intermediate, and advanced training paths",
  "Open and Pro category intensity rules",
  "Weak-station personalization",
  "Weekly progression phases",
  "Running, strength, skills, simulation, and recovery sessions",
  "Race readiness concept for future scoring",
];

export default function Home() {
  return (
    <main className="app-shell">
      <Navbar />

      <section className="hero-visual relative overflow-hidden">
        <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl items-center gap-10 px-5 py-16 lg:grid-cols-[1.08fr_0.92fr]">
          <div>
            <p className="mb-5 inline-flex rounded-lg border border-volt/30 bg-volt/10 px-4 py-2 text-xs font-black uppercase tracking-[0.24em] text-volt">
              Personalized HYROX Race Prep
            </p>
            <h1 className="max-w-5xl text-5xl font-black uppercase leading-[0.96] text-white md:text-7xl lg:text-8xl">
              Train Smarter. Race Harder. Conquer HYROX.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-white/70 md:text-xl">
              Personalized HYROX training plans based on your fitness level,
              race goal, weaknesses, and preparation timeline.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button href="/form">Start Your Plan</Button>
              <Button href="#how-it-works" variant="secondary">
                View How It Works
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <StatCard label="Running" value="1KM" accent="volt" />
            <StatCard label="Strength" value="SLED" accent="electric" />
            <StatCard label="HYROX Skills" value="9" accent="ember" />
            <StatCard label="Race Readiness" value="100" accent="volt" />
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20">
        <SectionTitle kicker="HYROX Planner" title="From Input To Race Plan">
          Zone 5 turns your current level, race target, and weak stations
          into a structured training plan you can actually follow.
        </SectionTitle>

        <div className="grid gap-5 md:grid-cols-3">
          {steps.map((step, index) => (
            <article key={step.title} className="panel rounded-lg p-6">
              <p className="text-sm font-black uppercase tracking-[0.22em] text-volt">
                Step {index + 1}
              </p>
              <h3 className="mt-4 text-2xl font-black uppercase text-white">
                {step.title}
              </h3>
              <p className="mt-3 leading-7 text-white/60">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-20">
        <SectionTitle kicker="Cardio Lab" title="Build Your Engine. Push Zone 5.">
          Generate a one-week cardio plan for running, cycling, swimming,
          marathon-style endurance, VO2 max, or mixed conditioning.
        </SectionTitle>

        <div className="grid gap-5 md:grid-cols-3">
          {cardioSteps.map((step, index) => (
            <article key={step.title} className="panel rounded-lg p-6">
              <p className="text-sm font-black uppercase tracking-[0.22em] text-electric">
                Lab {index + 1}
              </p>
              <h3 className="mt-4 text-2xl font-black uppercase text-white">
                {step.title}
              </h3>
              <p className="mt-3 leading-7 text-white/60">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-white/10 bg-white/[0.025] px-5 py-20">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-sm font-black uppercase tracking-[0.28em] text-electric">
              Why Zone 5
            </p>
            <h2 className="mt-3 text-4xl font-black uppercase leading-tight md:text-5xl">
              Built For The Race, Not Generic Fitness.
            </h2>
            <p className="mt-5 leading-8 text-white/70">
              HYROX performance is a mix of running endurance, station skill,
              strength endurance, transitions, and pacing. The planner is shaped
              around those demands from the first screen.
            </p>
          </div>

          <div id="features" className="grid gap-4 sm:grid-cols-2">
            {features.map((feature) => (
              <div
                key={feature}
                className="rounded-lg border border-white/10 bg-carbon/70 p-5 transition hover:border-volt/40 hover:bg-white/[0.04]"
              >
                <p className="font-bold leading-7 text-white/80">{feature}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="panel grid gap-8 rounded-lg p-7 md:p-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="text-sm font-black uppercase tracking-[0.28em] text-ember">
              AI Coach
            </p>
            <h2 className="mt-3 text-4xl font-black uppercase leading-tight md:text-5xl">
              Stuck With Your Plan? Ask The Coach.
            </h2>
            <p className="mt-5 leading-8 text-white/70">
              Use the AI Coach when your plan feels too hard, you miss
              sessions, your equipment is limited, or your diet needs a
              performance adjustment.
            </p>
            <div className="mt-7">
              <Button href="/ai-coach" variant="danger">
                Ask AI Coach
              </Button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              "Adjust plan difficulty",
              "Handle missed workouts",
              "Work around limited equipment",
              "Improve diet and energy",
            ].map((item) => (
              <div
                key={item}
                className="rounded-lg border border-ember/20 bg-ember/10 p-5 transition hover:border-ember/50 hover:bg-ember/15"
              >
                <p className="font-black uppercase tracking-[0.14em] text-ember">
                  {item}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20">
        <div className="panel grid gap-8 rounded-lg p-7 md:p-10 lg:grid-cols-[1fr_0.8fr]">
          <div>
            <p className="text-sm font-black uppercase tracking-[0.28em] text-ember">
              Race Readiness Concept
            </p>
            <h2 className="mt-3 text-4xl font-black uppercase leading-tight md:text-5xl">
              Know What Needs Work Before Race Day.
            </h2>
            <p className="mt-5 leading-8 text-white/70">
              The backend already includes a readiness score concept across
              running, strength, HYROX skill, consistency, and recovery. This
              frontend is ready to display richer readiness insights in the next
              product stage.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <StatCard label="Running" value="25" accent="electric" />
            <StatCard label="Strength" value="25" accent="volt" />
            <StatCard label="HYROX Skill" value="25" accent="ember" />
            <StatCard label="Recovery" value="10" accent="electric" />
          </div>
        </div>
      </section>
    </main>
  );
}
