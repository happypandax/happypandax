export function PageTitle({ title }: { title?: string }) {
  return (
    <title>{title ? title + ' - ' + global.app.title : global.app.title}</title>
  );
}
