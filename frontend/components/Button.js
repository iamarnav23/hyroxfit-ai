import Link from "next/link";

const styles = {
  primary:
    "bg-volt text-carbon hover:bg-white shadow-glow border border-volt/50",
  secondary:
    "bg-white/5 text-white hover:bg-white/10 border border-white/20",
  danger:
    "bg-ember text-white hover:bg-ember/90 border border-ember/50",
};

export default function Button({
  children,
  href,
  variant = "primary",
  className = "",
  ...props
}) {
  const base =
    "inline-flex min-h-12 items-center justify-center rounded-lg px-5 py-3 text-sm font-black uppercase tracking-wide transition duration-200 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0";
  const classes = `${base} ${styles[variant]} ${className}`;

  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
