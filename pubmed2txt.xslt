<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                >

  <xsl:output method="text"/>

  <xsl:template match="/">
    <xsl:apply-templates select="MedlineCitationSet/MedlineCitation/Article"/>
  </xsl:template>

  <xsl:template match="Article">
    <xsl:apply-templates select="ArticleTitle|Abstract/AbstractText"/>
  </xsl:template>

  <xsl:template match="ArticleTitle|AbstractText">
    <xsl:value-of select="."/>
    <xsl:text>&#x0a;</xsl:text>
  </xsl:template>
</xsl:stylesheet>