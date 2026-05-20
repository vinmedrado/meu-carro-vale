import { Camera, ImagePlus, UploadCloud, X } from 'lucide-react';
import { useState } from 'react';

export function PhotoUpload({ photos, onFiles, onRemove }: { photos: string[]; onFiles: (files: FileList | File[]) => void; onRemove: (index: number) => void }) {
  const [dragging, setDragging] = useState(false);
  return (
    <div className="space-y-4">
      <label
        className={`upload-zone real-upload ${dragging ? 'upload-active' : ''}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          onFiles(event.dataTransfer.files);
        }}
      >
        <input className="sr-only" type="file" accept="image/*" multiple onChange={(event) => event.target.files && onFiles(event.target.files)} />
        <UploadCloud size={36} />
        <h3>Envie fotos reais do veículo</h3>
        <p>Arraste as imagens ou toque para selecionar. Frente, traseira, laterais, painel e interior ajudam a valorizar o laudo e o anúncio.</p>
        <span className="upload-action"><ImagePlus size={16} /> Selecionar imagens</span>
      </label>
      {photos.length > 0 ? (
        <div className="photo-grid">
          {photos.map((photo, index) => (
            <div className="photo-card mcv-soft-enter" key={`${photo}-${index}`}>
              {photo.startsWith('data:') ? <img src={photo} alt={`Foto ${index + 1} do veículo`} /> : <div className="photo-placeholder"><Camera size={26} /><span>{photo}</span></div>}
              <button type="button" onClick={() => onRemove(index)} aria-label="Remover foto"><X size={15} /></button>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-upload"><Camera size={18} /> Nenhuma imagem adicionada ainda.</div>
      )}
    </div>
  );
}
