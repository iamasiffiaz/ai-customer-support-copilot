export default function Select({ label, options = [], className = '', ...props }) {
  return (
    <label className={`field block ${className}`}>
      {label ? <span>{label}</span> : null}
      <select className="field-control" {...props}>
        {options.map((opt) => {
          const value = typeof opt === 'string' ? opt : opt.value
          const labelText = typeof opt === 'string' ? opt : opt.label
          return (
            <option key={value} value={value}>
              {labelText}
            </option>
          )
        })}
      </select>
    </label>
  )
}
