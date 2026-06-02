export default function SectionTitle({ kicker, title, children }) {
  return (
    <div className="mx-auto mb-10 max-w-3xl text-center">
      <p className="text-sm font-black uppercase tracking-[0.28em] text-volt">
        {kicker}
      </p>
      <h2 className="mt-3 text-3xl font-black uppercase leading-tight text-white md:text-5xl">
        {title}
      </h2>
      {children && (
        <p className="mt-4 text-base leading-7 text-white/70 md:text-lg">
          {children}
        </p>
      )}
    </div>
  );
}
