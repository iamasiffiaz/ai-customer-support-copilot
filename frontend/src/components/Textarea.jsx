export default function Textarea({ label, className = '', rows = 5, ...props }) {
  return (
    <label className={`field block ${className}`}>
      {label ? <span>{label}</span> : null}
      <textarea rows={rows} className="field-control" {...props} />
    </label>
  )
}
