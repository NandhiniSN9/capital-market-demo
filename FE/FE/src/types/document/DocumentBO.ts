export interface DocumentSectionBO {
  id: string;
  title: string;
  pageStart: number;
  pageEnd: number;
  content: string;
}

export interface DocumentBO {
  id: string;
  name: string;
  shortName: string;
  type: 'financial' | 'legal' | 'operational' | 'market';
  subType: string;
  company: string;
  period: string;
  pageCount: number;
  uploadDate: string;
  status: 'ready' | 'processing';
  sections: DocumentSectionBO[];
}
