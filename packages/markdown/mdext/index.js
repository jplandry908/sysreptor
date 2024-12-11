import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import remarkStringify from 'remark-stringify';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { merge } from 'lodash-es';
import 'highlight.js/styles/default.css';

import { remarkFootnotes, remarkToRehypeHandlersFootnotes, remarkToRehypeHandersFootnotesPreview, rehypeFootnoteSeparator, rehypeFootnoteSeparatorPreview } from './mdext/footnotes.js';
import { remarkStrikethrough, remarkTaskListItem } from './mdext/gfm.js';
import { rehypeConvertAttrsToStyle, rehypeLinkTargetBlank, rehypeRewriteImageSources, rehypeRewriteFileLinks, rehypeTemplates, rehypeRawFixSelfClosingTags, rehypeRawFixPassthroughStitches } from './mdext/rehypePlugins.js';
import { remarkAttrs, remarkToRehypeAttrs } from './mdext/attrs.js';
import { remarkFigure, remarkToRehypeHandlersFigure } from './mdext/image.js';
import { remarkTables, remarkTableCaptions, remarkToRehypeHandlersTableCaptions, rehypeTableCaptions } from './mdext/tables.js';
import { rehypeReferenceLink, rehypeReferenceLinkPreview } from './mdext/reference.js';
import { annotatedTextParse } from './editor/annotatedtext';
import { remarkTemplateVariables, remarkToRehypeTemplateVariables, rehypeTemplateVariables } from './mdext/templates.js';
import { remarkTodoMarker } from './mdext/todo.js';
import { rehypeHighlightCode } from './mdext/codeHighlight.js';
import { modifiedCommonmarkFeatures } from './mdext/modified-commonmark.js';
import { rehypeStringify } from './mdext/stringify.js';

const allClasses = ['className', /^.*$/];
const rehypeSanitizeSchema = merge({}, defaultSchema, {
  allowComments: true,
  clobberPrefix: null,
  tagNames: [
    // Custom components
    'footnote', 'template', 'ref', 'pagebreak', 'markdown', 'mermaid-diagram', 
    // Regular HTML tags not included in default schema
    'figure', 'figcaption', 'caption', 'mark', 'u',
    'abbr', 'bdo', 'cite', 'dfn', 'time', 'var', 'wbr',
  ].concat(defaultSchema.tagNames),
  attributes: {
    '*': ['className', 'style', 'data*', 'v-if', 'v-else-if', 'v-else', 'v-for', 'v-bind', 'v-on', 'v-show', 'v-pre', 'v-text'].concat(defaultSchema.attributes['*']),
    'a': ['download', 'target', 'rel', allClasses].concat(defaultSchema.attributes['a']),
    'img': ['loading'].concat(defaultSchema.attributes['img']),
    'code': [allClasses].concat(defaultSchema.attributes['code']),
    'h2': [allClasses].concat(defaultSchema.attributes['h2']),
    'ul': [allClasses].concat(defaultSchema.attributes['ul']),
    'ol': [allClasses].concat(defaultSchema.attributes['ol']),
    'li': [allClasses].concat(defaultSchema.attributes['li']),
    'section': [allClasses].concat(defaultSchema.attributes['section']),
    'ref': ['to', ':to'],
    'markdown': ['text', ':text'],
  }
});


export function markdownParser() {
  return unified()
    .use(modifiedCommonmarkFeatures)
    .use(remarkFootnotes)
    .use(remarkTables)
    .use(remarkTableCaptions)
    .use(remarkStrikethrough)
    .use(remarkTaskListItem)
    .use(remarkTemplateVariables)
    .use(remarkAttrs)
    .use(remarkFigure)
    .use(remarkTodoMarker);
}


/**
 * 
 * @param {string} text 
 * @returns {string}
 */
export function formatMarkdown(text) {
  const md = markdownParser()
    .use(remarkParse)
    .use(remarkStringify, {
      fence: '`',
      fences: true,
      bullet: '*',
      strong: '*',
      emphasis: '_',
    });
  return md.processSync(text).value;
}

/**
 * 
 * @param {string} text 
 * @param {*} options 
 * @returns {string}
 */
export function renderMarkdownToHtml(text, {preview = false, rewriteFileSource = null, rewriteReferenceLink = null} = {}) {
  let md = markdownParser()
      .use(remarkParse)
      .use(remarkRehype, { 
        allowDangerousHtml: true, 
        footnoteLabelTagName: 'h4',
        handlers: {
          ...(preview ? remarkToRehypeHandersFootnotesPreview : remarkToRehypeHandlersFootnotes),
          ...remarkToRehypeHandlersFigure,
          ...remarkToRehypeHandlersTableCaptions,
          ...remarkToRehypeAttrs,
          ...remarkToRehypeTemplateVariables,
        }
      })
      .use(rehypeTableCaptions)
      .use(rehypeHighlightCode, { preview })
      .use(rehypeRawFixSelfClosingTags)
      .use(rehypeRaw, { passThrough: ['templateVariable']})
      .use(rehypeTemplates)
      .use(rehypeRawFixPassthroughStitches)
      .use(rehypeTemplateVariables, { preview })
      .use(rehypeConvertAttrsToStyle)
      .use(preview ? rehypeFootnoteSeparatorPreview : rehypeFootnoteSeparator)
      .use(preview ? rehypeReferenceLinkPreview : rehypeReferenceLink, { rewriteReferenceLink })
      .use(rehypeRewriteImageSources, {rewriteImageSource: rewriteFileSource})
      .use(rehypeRewriteFileLinks, {rewriteFileUrl: rewriteFileSource})
      .use(rehypeLinkTargetBlank);
    if (preview) {
      md = md.use(rehypeSanitize, rehypeSanitizeSchema);
    }
    md = md.use(rehypeStringify);

    // Normalize linebreaks
    text = text.replace(/\r\n/g, '\n');

    // const mdAst = md.parse(text);
    // console.log('MarkdownAST', mdAst);
    // const rehypeAst = md.runSync(mdAst);
    // console.log('RehypeAST', rehypeAst);
    // const mdHtml = md.stringify(rehypeAst);
    // console.log('HTML', mdHtml);
    const mdHtml = md.processSync(text).value;
    return mdHtml;
}

/**
 * 
 * @param {string} text 
 * @returns {import('./editor/annotatedtext').AnnotatedText[]}
 */
export function markdownToAnnotatedText(text) {
  const md = markdownParser()
    .use(annotatedTextParse);
  const at = md.parse(text);
  // console.log('AnnotatedText', at);
  return at;
}


