import * as bytemd from "bytemd";
import React, { useRef, useEffect, useMemo } from "react";
const Editor = ({ onChange, ...props }) => {
  const ed = useRef();
  const el = useRef(null);
  const onChangeRef = useRef();
  useEffect(() => {
    if (!el.current)
      return;
    const editor = new bytemd.Editor({
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
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);
  useEffect(() => {
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
  const elRef = useRef(null);
  const file = useMemo(() => {
    try {
      return bytemd.getProcessor({ sanitize, plugins, remarkRehype }).processSync(value);
    } catch (err) {
      console.error(err);
    }
  }, [value, sanitize, plugins, remarkRehype]);
  useEffect(() => {
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
export {
  Editor,
  Viewer
};
