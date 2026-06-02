export default function StatCard({ label, value, accent = "volt" }) {
  const accentClasses = {
    volt: "text-volt border-volt/40",
    electric: "text-electric border-electric/40",
    ember: "text-ember border-ember/40",
  };

  return (
    <div className={`panel rounded-lg p-5 transition duration-200 hover:-translate-y-1 ${accentClasses[accent]}`}>
      <p className="text-2xl font-black">{value}</p>
      <p className="mt-2 text-sm font-bold uppercase tracking-[0.18em] text-white/50">
        {label}
      </p>
    </div>
  );
}
