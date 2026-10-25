type TimelineEventProps = {
  date: string;
  title: string;
  description: string;
};

export default function TimelineEvent({
  date,
  title,
  description,
}: TimelineEventProps) {
  return (
    <div className="timeline-event">
      <div className="timeline-dot" />

      <div>
        <div className="timeline-date">{date}</div>

        <div className="timeline-title">
          {title}
        </div>

        <div className="timeline-description">
          {description}
        </div>
      </div>
    </div>
  );
}