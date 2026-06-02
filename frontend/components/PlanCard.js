export default function PlanCard({ children, className = "" }) {
  return (
    <section className={`panel rounded-lg p-5 md:p-6 ${className}`}>
      {children}
    </section>
  );
}
