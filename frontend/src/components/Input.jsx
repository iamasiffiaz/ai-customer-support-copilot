export default function Input({ label, className = '', ...props }) {
  return (
    <label className={`field block ${className}`}>
      {label ? <span>{label}</span> : null}
      <input className="field-control" {...props} />
    </label>
  )
}
