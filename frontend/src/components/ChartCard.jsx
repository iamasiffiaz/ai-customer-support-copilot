export default function ChartCard({ title, children, action }) {
  return (
    <div className="panel overflow-hidden">
      <div className="panel-header">
        <h3>{title}</h3>
        {action}
      </div>
      <div className="panel-body h-64">{children}</div>
    </div>
  )
}
