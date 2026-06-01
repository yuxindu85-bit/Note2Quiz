import UploadBox from '../components/UploadBox';

export default function Upload() {
  return (
    <section className="upload-page">
      <div className="page-heading">
        <p className="eyebrow">Create</p>
        <h1>Upload lecture material</h1>
        <p>
          Choose a file, let Note2Quiz extract the text, then review a generated pack with tabs for
          every study format.
        </p>
      </div>
      <UploadBox />
    </section>
  );
}
