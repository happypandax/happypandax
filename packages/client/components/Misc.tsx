export function PageTitle({ title }: { title?: string }) {
  if (!global.app.IS_SERVER) {
    document.title = title
      ? title + ' - ' + global.app.title
      : global.app.title;
  }
  return null;
}

export default {};
