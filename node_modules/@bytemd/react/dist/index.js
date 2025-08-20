"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const bytemd = require("bytemd");
const React = require("react");
function _interopNamespaceDefault(e) {
  const n = Object.create(null, { [Symbol.toStringTag]: { value: "Module" } });
  if (e) {
    for (const k in e) {
      if (k !== "default") {
        const d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: () => e[k]
        });
      }
    }
  }
  n.default = e;
  return Object.freeze(n);
}
const bytemd__namespace = /* @__PURE__ */ _interopNamespaceDefault(bytemd);
const Editor = ({ onChange, ...props }) => {
  const ed = React.useRef();
  const el = React.useRef(null);
  const onChangeRef = React.useRef();
  React.useEffect(() => {
    if (!el.current)
      return;
    const editor = new bytemd__namespace.Editor({
      target: el.current,
      props
    });
    editor.$on("change", (e) => {
      var _a;
      (_a = onChangeRef.current) == null ? void 0 : _a.call(onChangeRef, e.detail.value);
    });
    ed.current = editor;
    return () => {
      editor.$destroy();
    };
  }, []);
  React.useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);
  React.useEffect(() => {
    var _a;
    (_a = ed.current) == null ? void 0 : _a.$set(props);
  }, [props]);
  return /* @__PURE__ */ React.createElement("div", { ref: el });
};
const Viewer = ({
  value,
  sanitize,
  plugins,
  remarkRehype
}) => {
  var _a;
  const elRef = React.useRef(null);
  const file = React.useMemo(() => {
    try {
      return bytemd__namespace.getProcessor({ sanitize, plugins, remarkRehype }).processSync(value);
    } catch (err) {
      console.error(err);
    }
  }, [value, sanitize, plugins, remarkRehype]);
  React.useEffect(() => {
    const markdownBody = elRef.current;
    if (!markdownBody || !file)
      return;
    const cbs = plugins == null ? void 0 : plugins.map(
      ({ viewerEffect }) => viewerEffect == null ? void 0 : viewerEffect({ markdownBody, file })
    );
    return () => {
      cbs == null ? void 0 : cbs.forEach((cb) => cb && cb());
    };
  }, [file, plugins]);
  return /* @__PURE__ */ React.createElement(
    "div",
    {
      onClick: (e) => {
        var _a2, _b;
        const $ = e.target;
        if ($.tagName !== "A")
          return;
        const href = $.getAttribute("href");
        if (!(href == null ? void 0 : href.startsWith("#")))
          return;
        (_b = (_a2 = elRef.current) == null ? void 0 : _a2.querySelector("#user-content-" + href.slice(1))) == null ? void 0 : _b.scrollIntoView();
      },
      ref: elRef,
      className: "markdown-body",
      dangerouslySetInnerHTML: { __html: (_a = file == null ? void 0 : file.toString()) != null ? _a : "" }
    }
  );
};
exports.Editor = Editor;
exports.Viewer = Viewer;
