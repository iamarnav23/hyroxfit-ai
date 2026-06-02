export default function FormInput({
  label,
  name,
  value,
  onChange,
  type = "text",
  placeholder = "",
  helperText = "",
  required = true,
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold uppercase tracking-[0.1em] text-white/60 sm:tracking-[0.16em]">
        {label}
      </span>
      <input
        className="input-field"
        name={name}
        value={value}
        type={type}
        placeholder={placeholder}
        required={required}
        onChange={onChange}
      />
      {helperText && (
        <p className="mt-2 text-xs font-semibold leading-5 text-white/50">
          {helperText}
        </p>
      )}
    </label>
  );
}
