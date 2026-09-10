import { XMLParser } from 'fast-xml-parser';
import { PaperSection, PaperReference } from '../modules/papers/papers.types';

export interface GrobidResult {
  title: string;
  authors: string[];
  abstract: string;
  sections: PaperSection[];
  references: PaperReference[];
  fullText: string;
}

export async function extractWithGrobid(pdfBuffer: Buffer): Promise<GrobidResult> {
  const formData = new FormData();
  formData.append('input', new Blob([new Uint8Array(pdfBuffer)], { type: 'application/pdf' }));
  formData.append('consolidateHeader', '0');
  formData.append('consolidateCitations', '0');

  const response = await fetch('http://localhost:8070/api/processFulltextDocument', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`GROBID failed with status ${response.status}: ${await response.text()}`);
  }

  const xmlText = await response.text();
  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
    textNodeName: '#text',
  });
  
  const obj = parser.parse(xmlText);
  const tei = obj.TEI;

  const header = tei?.teiHeader;
  const fileDesc = header?.fileDesc;
  const titleStmt = fileDesc?.titleStmt;
  
  let title = '';
  if (titleStmt?.title) {
    title = extractTextFromNode(titleStmt.title);
  }

  const authors: string[] = [];
  const authorNodes = fileDesc?.sourceDesc?.biblStruct?.analytic?.author;
  if (authorNodes) {
    const list = Array.isArray(authorNodes) ? authorNodes : [authorNodes];
    for (const author of list) {
      if (author.persName) {
        const first = author.persName.forename 
          ? (Array.isArray(author.persName.forename) 
              ? author.persName.forename.map((f: any) => extractTextFromNode(f)).join(' ') 
              : extractTextFromNode(author.persName.forename)) 
          : '';
        const last = author.persName.surname ? extractTextFromNode(author.persName.surname) : '';
        if (first || last) {
          authors.push(`${first} ${last}`.trim());
        }
      }
    }
  }

  let abstract = '';
  const abstractNode = header?.profileDesc?.abstract?.div?.p;
  if (abstractNode) {
    abstract = extractTextFromNode(abstractNode);
  }

  const sections: PaperSection[] = [];
  const bodyDivs = tei?.text?.body?.div;
  let fullText = abstract + '\n\n';
  
  if (bodyDivs) {
    const divs = Array.isArray(bodyDivs) ? bodyDivs : [bodyDivs];
    for (const div of divs) {
      const name = div.head ? extractTextFromNode(div.head) : 'Section';
      const content = extractTextFromNode(div.p);
      if (content.trim()) {
        sections.push({
          name: name.trim(),
          content: content.trim(),
          orderIndex: sections.length,
        });
        fullText += `${name}\n${content}\n\n`;
      }
    }
  }

  const references: PaperReference[] = [];
  const listBibl = tei?.text?.back?.div?.listBibl?.biblStruct;
  if (listBibl) {
    const bibls = Array.isArray(listBibl) ? listBibl : [listBibl];
    for (let i = 0; i < bibls.length; i++) {
      const bibl = bibls[i];
      const xmlId = bibl['@_xml:id'] || `b${i}`;
      const citationKey = xmlId;
      
      const analytic = bibl.analytic || {};
      const monogr = bibl.monogr || {};
      
      let refTitle = '';
      if (analytic.title) {
        refTitle = extractTextFromNode(analytic.title);
      } else if (monogr.title) {
        refTitle = extractTextFromNode(monogr.title);
      }

      const refAuthors: string[] = [];
      const refAuthorNodes = analytic.author || monogr.author;
      if (refAuthorNodes) {
        const alist = Array.isArray(refAuthorNodes) ? refAuthorNodes : [refAuthorNodes];
        for (const a of alist) {
           if (a.persName) {
            const first = a.persName.forename 
              ? (Array.isArray(a.persName.forename) 
                  ? a.persName.forename.map((f: any) => extractTextFromNode(f)).join(' ') 
                  : extractTextFromNode(a.persName.forename)) 
              : '';
            const last = a.persName.surname ? extractTextFromNode(a.persName.surname) : '';
            if (first || last) {
              refAuthors.push(`${first} ${last}`.trim());
            }
          }
        }
      }

      let year = '';
      const imprint = monogr.imprint;
      if (imprint?.date) {
        const dates = Array.isArray(imprint.date) ? imprint.date : [imprint.date];
        for (const d of dates) {
          if (d['@_type'] === 'published' && d['@_when']) {
            year = d['@_when'].substring(0, 4);
            break;
          }
        }
      }

      references.push({
        citationKey,
        title: refTitle.trim(),
        authors: refAuthors,
        year,
        rawText: `${refAuthors.join(', ')}. "${refTitle.trim()}". ${year}`,
        relationship: 'referenced work',
        importance: 1,
      });
    }
  }

  return {
    title,
    authors,
    abstract,
    sections,
    references,
    fullText: fullText.trim()
  };
}

function extractTextFromNode(node: any): string {
  if (node === null || node === undefined) return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) {
    return node.map(extractTextFromNode).join(' ');
  }
  
  let text = '';
  for (const key of Object.keys(node)) {
    if (key === '#text') {
      text += node[key] + ' ';
    } else if (!key.startsWith('@_')) {
      text += extractTextFromNode(node[key]) + ' ';
    }
  }
  return text.replace(/\s+/g, ' ').trim();
}
