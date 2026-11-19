function CodeBlock(block)
  if block.classes:includes("math") then
    return pandoc.Para({ pandoc.Math("DisplayMath", block.text) })
  end
end
