import { Link, useParams } from "react-router-dom";
import { topics } from "../learn";

export function Learn() {
  return (
    <div>
      <h1 className="text-2xl font-extrabold sm:text-3xl">Learn</h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Short, plain-language explanations of what the numbers mean and how they were checked. Start with the first one.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {topics.map((t, i) => (
          <Link
            key={t.slug}
            to={`/learn/${t.slug}`}
            className="group rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100 transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-linear-to-br from-indigo-500 to-fuchsia-500 text-xs font-bold text-white">
              {i + 1}
            </span>
            <h2 className="mt-3 font-bold group-hover:text-indigo-700">{t.title}</h2>
            <p className="mt-1 text-sm text-slate-500">{t.summary}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function LearnTopic() {
  const { slug } = useParams();
  const index = topics.findIndex((t) => t.slug === slug);
  if (index < 0) {
    return (
      <div>
        <p className="text-slate-600">That Learn page doesn't exist.</p>
        <Link to="/learn" className="font-semibold text-indigo-600 underline">Back to Learn</Link>
      </div>
    );
  }
  const topic = topics[index];
  const next = topics[index + 1];
  return (
    <article className="mx-auto max-w-2xl">
      <Link to="/learn" className="text-sm font-semibold text-indigo-600 hover:underline">← All topics</Link>
      <h1 className="mt-3 text-2xl font-extrabold sm:text-3xl">{topic.title}</h1>
      <div className="mt-5 space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-indigo-100 sm:p-7">
        {topic.body.map((b, i) => (
          <section key={i}>
            {b.heading && <h2 className="mb-1 font-bold text-indigo-700">{b.heading}</h2>}
            <p className="leading-relaxed text-slate-700">{b.text}</p>
          </section>
        ))}
      </div>
      {next && (
        <Link
          to={`/learn/${next.slug}`}
          className="mt-5 inline-block rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Next: {next.title} →
        </Link>
      )}
    </article>
  );
}
